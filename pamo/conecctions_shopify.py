from pamo.constants import *
import requests
import pandas as pd
import json
from pamo_bots.models import OrdersShopify, ProductsOrders, TrakingOrders
import time
import os
from quote_print.models import SodimacOrders
from pamo_bots.models import LastCursor
from pamo.queries import GET_VARIANT_ID, GET_INVENTORY, GET_ORDERS
from dateutil import parser as dateutil_parser


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
                print(f"No se encontro el SKU en shopify: {row['SKU']}")
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
            if None in variant_id:
                continue
            for i in range(len(variant_id)):
                if variant_id[i]:
                    products.append(
                        {
                            "variant_id": variant_id[i],
                            "quantity": int(cantidad[i]),
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

    def fetch_orders_shopify(self):
        last = LastCursor.objects.first()
        cursor_str = last.cursor

        all_nodes = []
        response = self.request_graphql(GET_ORDERS.format(cursor=cursor_str))
        data = response.json()["data"]["orders"]
        all_nodes.extend([edge["node"] for edge in data["edges"]])

        while data["pageInfo"]["hasNextPage"]:
            time.sleep(20)
            end_cursor = data["pageInfo"]["endCursor"]
            response = self.request_graphql(GET_ORDERS.format(cursor={end_cursor}))
            data = response.json()["data"]["orders"]
            all_nodes.extend([edge["node"] for edge in data["edges"]])

        end_cursor = data["pageInfo"]["endCursor"]
        if end_cursor:
            LastCursor.objects.update_or_create(pk=1, defaults={"cursor": end_cursor})

        return all_nodes

    def format_orders_response(self, raw_nodes):
        formatted = []
        for node in raw_nodes:
            customer = node.get("customer") or {}
            address = customer.get("defaultAddress") or {}
            line_items = node.get("lineItems", {}).get("nodes", [])
            order_is_cancelled = True if node.get('cancelledAt') else False
            products = []
            total_order = 0.0
            for item in line_items:
                total_line = float(
                    item.get("originalTotalSet", {})
                    .get("presentmentMoney", {})
                    .get("amount", 0)
                )
                quantity = item.get("quantity") or 1
                unit_cost = round(total_line / quantity, 2)
                total_order += total_line
                products.append({
                    "sku": item.get("sku"),
                    "name": item.get("name", "")[0:99],
                    "quantity": quantity,
                    "unit_cost": unit_cost,
                    "total_cost": total_line,
                })
            gateways = node.get("paymentGatewayNames") or []
            gateways_name = None
            if gateways:
                gateways_name = ("Mercado Pago" if 'mercado' in gateways[0].lower() else 'Addi Payment' if 'astroselling' in gateways[0].lower() else gateways[0])

            fulfillments = node.get("fulfillments") or []
            trackings = []
            for f in fulfillments:
                if f.get('status') == 'CANCELLED':
                    continue
                for t in (f.get("trackingInfo") or []):
                    trackings.append({
                        "shipping_company": t.get("company"),
                        "tracking_number": t.get("number"),
                        "url_traking": t.get("url"),
                    })

            formatted.append({
                "id": node.get("legacyResourceId"),
                "pedido": node.get("name", "").replace("#", ""),
                "created_at": node.get("createdAt"),
                "payment_method": gateways_name,
                "customer_name": customer.get("displayName"),
                "customer_id": address.get("company"),
                "total_cost": round(total_order, 2),
                "trackings": trackings,
                "products": products,
                "order_is_cancelled": order_is_cancelled
            })
        return formatted

    def save_orders_to_db(self, formatted_data):
        count = 0
        for order_data in formatted_data:
            if order_data.get('order_is_cancelled'):
                print(order_data)
            products = order_data.pop("products")
            trackings = order_data.pop("trackings")
            for i in trackings:
               i['tracking_number']= i['tracking_number'][0:50]
            order, created = OrdersShopify.objects.update_or_create(
                id=order_data["id"],
                defaults=order_data,
            )
            if not created:
                order.products.all().delete()
                order.traking.all().delete()
            ProductsOrders.objects.bulk_create([
                ProductsOrders(order=order, **p) for p in products
            ])
            TrakingOrders.objects.bulk_create([
                TrakingOrders(order=order, **t) for t in trackings
            ])
            count += 1
        return count

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

    def create_order_from_webhook(self, data):
        order_id = str(data.get('id'))
        pedido   = data.get('name')
        created_at = dateutil_parser.parse(data.get('created_at'))
        gateways = data.get('payment_gateway_names') or []
        gw = gateways[0].lower() if gateways else ''
        payment_method = (
            'Mercado Pago'  if 'mercado'      in gw else
            'Addi Payment'  if 'astroselling'  in gw else
            (gateways[0] if gateways else None)
        )
        customer_name = (data.get('billing_address') or {}).get('name')
        customer_id   = str(data.get('customer', {}).get('id') or '')
        line_items = data.get('line_items', [])
        total_cost = sum(
            round(float(i.get('quantity', 0)) * float(i.get('price', 0)))
            for i in line_items
        )
        order, _ = OrdersShopify.objects.update_or_create(
            id=order_id,
            defaults={
                'pedido':          pedido,
                'created_at':      created_at,
                'payment_method':  payment_method,
                'customer_name':   customer_name,
                'customer_id':     customer_id,
                'total_cost':      total_cost,
            }
        )
        ProductsOrders.objects.filter(order=order).delete()
        ProductsOrders.objects.bulk_create([
            ProductsOrders(
                order=order,
                sku=item.get('sku'),
                name=(item.get('name') or '')[:99],
                unit_cost=round(float(item.get('price', 0))),
                quantity=item.get('quantity', 1),
                total_cost=round(float(item.get('quantity', 0)) * float(item.get('price', 0))),
            )
            for item in line_items
        ])
        fulfillments = data.get('fulfillments') or []
        if fulfillments:
            TrakingOrders.objects.filter(order=order).delete()
            new_trackings = []
            for f in fulfillments:
                tracking_numbers = f.get('tracking_numbers') or []
                tracking_urls    = f.get('tracking_urls') or []
                shipping_company = f.get('tracking_company')
                for i, number in enumerate(tracking_numbers):
                    new_trackings.append(TrakingOrders(
                        order=order,
                        tracking_number=number,
                        url_traking=tracking_urls[i] if i < len(tracking_urls) else None,
                        shipping_company=shipping_company,
                    ))
            TrakingOrders.objects.bulk_create(new_trackings)