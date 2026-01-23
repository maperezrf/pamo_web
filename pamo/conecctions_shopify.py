from pamo.constants import *
import requests
import pandas as pd
import json

# from pamo.functions import make_json
import os
from quote_print.models import SodimacOrders
from pamo.queries import GET_VARIANT_ID, GET_INVENTORY


class ConnectionsShopify:

    headers_shopify = {}
    orders = pd.DataFrame()
    not_found_skus = []

    def __init__(self) -> None:
        self.headers_shopify = {
            "X-Shopify-Access-Token": ACCES_TOKEN,
            "Content-Type": "application/json",
        }
        self.not_found_skus = []

    def set_orders_df(self, orders):
        self.orders = orders

    def request_graphql(self, query, variables=None):
        return requests.post(
            URL_GRAPHQL,
            headers=self.headers_shopify,
            data=json.dumps({"query": query, "variables": variables}),
        )

    def get_rest(self, url):
        return requests.get(url, headers=self.headers_shopify)

    def get_variant_id(self):
        self.orders["variant_id"] = None
        self.not_found_skus = []  # Reset list
        for i, row in self.orders.iterrows():
            query = GET_VARIANT_ID.format(skus=str(row["SKU"]).strip())
            response = requests.post(
                URL_GRAPHQL,
                headers=self.headers_shopify,
                data=json.dumps({"query": query}),
            )
            id_searching = (
                response.json()
                .get("data", {})
                .get("productVariants", {})
                .get("edges", [])
            )
            if id_searching:
                variant_id = id_searching[0].get("node", {}).get("id", "")
                if variant_id:
                    variant_id = str(variant_id).replace(
                        "gid://shopify/ProductVariant/", ""
                    )
                    self.orders.loc[self.orders["SKU"] == row['SKU'], "variant_id"] = variant_id
                else:
                    print(f"No se encontro el SKU en shopify: {row['SKU']}")
                    self.not_found_skus.append(
                        {"ORDEN_COMPRA": row["ORDEN_COMPRA"], "SKU": row["SKU"]}
                    )
                    self.add_novelty(row["SKU"])
            else:
                print(f"No se encontro el SKU en shopify: {i}")
                self.not_found_skus.append(
                    {"ORDEN_COMPRA": row["ORDEN_COMPRA"], "SKU": row["SKU"]}
                )
                self.add_novelty(row["SKU"])
        return self.orders.loc[self.orders["variant_id"].notna()]

    def get_not_found_skus(self):
        return self.not_found_skus

    def add_novelty(self, sku):
        for i in self.orders.loc[self.orders["SKU"] == sku]["ORDEN_COMPRA"].unique():
            obj, _ = SodimacOrders.objects.get_or_create(id=i)
            obj.oc_shopify = f"No se encontro el SKU :{sku} en shopify"
            obj.save()

    def bucle_request(self, query, datatype):
        response = self.request_graphql(query.format(cursor=""))
        print(query.format(cursor=""))
        print(response.json())
        res = response.json()["data"][datatype]["edges"]
        print(res)
        daft_orders = make_json(res)
        print(daft_orders)
        has_next = response.json()["data"][datatype]["pageInfo"]["hasNextPage"]
        while has_next:
            response = self.request_graphql(
                query.format(
                    cursor=f",after:\"{response.json()['data'][datatype]['pageInfo']['endCursor']}\""
                )
            )
            res = response.json()["data"][datatype]["edges"]
            daft_orders.extend(make_json(res))
            has_next = response.json()["data"][datatype]["pageInfo"]["hasNextPage"]
        print(response.json())

    def create_orders(self):
        orders_gb = (
            self.orders.groupby("ORDEN_COMPRA")
            .agg({"variant_id": list, "CANTIDAD_SKU": list, "COSTO_SKU": list})
            .reset_index()
        )
        print(orders_gb.shape[0])
        print(len(orders_gb))
        data_log = {}
        data_log["success"] = []
        data_log["error"] = []
        for i in range(len(orders_gb)):
            products = []
            oc = orders_gb.iloc[i]["ORDEN_COMPRA"]
            cantidad = orders_gb.iloc[i]["CANTIDAD_SKU"]
            costo = orders_gb.iloc[i]["COSTO_SKU"]
            variant_id = orders_gb.iloc[i]["variant_id"]
            products = []
            for i in range(len(variant_id)):
                if variant_id[i]:
                    products.append(
                        {
                            "variant_id": variant_id[i],
                            "quantity": cantidad[i],
                            "price": costo[i],
                        }
                    )
                    data = {
                        "order": {
                            "line_items": products,
                            "customer": {"id": 7247084421397},
                            "financial_status": "pending",
                            "note": f"orden de compra: {oc}",
                            "tags": "SODIMAC",
                        }
                    }
                    try:
                        obj, _ = SodimacOrders.objects.get_or_create(id=oc)
                        response = requests.post(
                            URL_CREATE_ORDERS, headers=self.headers_shopify, json=data
                        )
                        if response.status_code == 201:
                            obj.oc_shopify = (
                                response.json().get("order", {}).get("order_number", {})
                            )
                            obj.save()
                            data_log["success"].append(oc)
                        else:
                            obj.oc_shopify = "Error al crear la orden"
                            obj.save()
                    except:
                        obj.oc_shopify = "Error al crear la orden"
                        obj.save()
                        data_log["error"].append(oc)
        return data_log

    def get_orders(self):
        return self.orders

    def get_inventory(self, df):
        for i in range(10):  # udf.shape[0]):
            print(df.iloc[i].sku)
            response = self.request_graphql(GET_INVENTORY.format(sku=df.iloc[i].sku))
            try:
                inventory = response.json()["data"]["products"]["edges"][0]["node"][
                    "variants"
                ]["edges"][0]["node"]["inventoryQuantity"]
                df.loc[i, "stock_shopyfi"] = inventory
                print(response.json())
            except Exception as e:
                print(f"No se encontro el SKU: {df.iloc[i].sku}")
                df.loc[i, "stock_shopyfi"] = "El SKU no se encontró"
        return df.loc[df["existencia"] != df["stock_shopyfi"]]
