from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from pamo.conecctions_shopify import ConnectionsShopify
from pamo.connections_sodimac import ConnectionsSodimac
from pamo.connections_airtable import connAirtable
from pamo.connections_melonn import connMelonn
from django.conf import settings
import datetime
from pamo.functions import create_file_products
from products.forms import fileForm
from pamo_bots.models import LogBotOrders, ProductsSodimac
from quote_print.models import SodimacOrders, SodimacKits
import pandas as pd
from pamo_bots.core_df import Core
import json
from pamo.constants import NOTIFICATIONS_RECIPENTS
import os
from django.contrib.auth.decorators import login_required
from pamo.connecctions_sigo import SigoConnection
from pamo.email_sender import EmailSender  # Importar la clase de email


@login_required
def sodimac_view(request):
    return render(request, "sodimac_view.html", context={})


def get_orders(request):
    logs = LogBotOrders.objects.all().order_by("-date")[:20]
    sodimac_orders = SodimacOrders.objects.all().order_by("-id")
    return render(request, "get_orders.html", context={"logs": logs, "sodimac_orders": sodimac_orders})


def manager_database(request):
    products = ProductsSodimac.objects.all()

    # Agrupar SodimacKits por kitnumber
    kits_qs = SodimacKits.objects.all().order_by('kitnumber', 'sku')
    kits_grouped = {}
    for kit in kits_qs:
        kn = kit.kitnumber
        if kn not in kits_grouped:
            kits_grouped[kn] = {'kitnumber': kn, 'ean': kit.ean, 'items': []}
        kits_grouped[kn]['items'].append({
            'id': kit.id,
            'sku': kit.sku,
            'quantity': kit.quantity,
            'ean': kit.ean,
        })

    data = {
        'table': products,
        'kits': list(kits_grouped.values()),
    }
    return render(request, "manager_database.html", context=data)


@login_required
def edit_product_sodimac(request, id):
    try:
        product = ProductsSodimac.objects.get(id=id)
    except ProductsSodimac.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Registro no encontrado'}, status=404)

    if request.method == 'PATCH':
        body = json.loads(request.body)
        field = body.get('field')
        value = body.get('value')
        allowed_fields = {'sku_sodimac', 'sku_pamo', 'ean'}
        if field not in allowed_fields:
            return JsonResponse({'success': False, 'message': 'Campo no permitido'}, status=400)
        setattr(product, field, value)
        product.save()
        return JsonResponse({'success': True})

    if request.method == 'DELETE':
        product.delete()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)


@login_required
def create_product_sodimac(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
    body = json.loads(request.body)
    product = ProductsSodimac.objects.create(
        sku_sodimac=body.get('sku_sodimac') or None,
        sku_pamo=body.get('sku_pamo') or None,
        ean=body.get('ean') or None,
    )
    return JsonResponse({'success': True, 'id': product.id})


@login_required
def edit_sodimac_kit(request, id):
    try:
        kit = SodimacKits.objects.get(id=id)
    except SodimacKits.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Registro no encontrado'}, status=404)

    if request.method == 'PATCH':
        body = json.loads(request.body)
        field = body.get('field')
        value = body.get('value')
        allowed_fields = {'kitnumber', 'sku', 'quantity', 'ean'}
        if field not in allowed_fields:
            return JsonResponse({'success': False, 'message': 'Campo no permitido'}, status=400)
        if field == 'quantity':
            value = int(value)
        setattr(kit, field, value)
        kit.save()
        return JsonResponse({'success': True})

    if request.method == 'DELETE':
        kit.delete()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)


@login_required
def create_sodimac_kit(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'}, status=405)
    body = json.loads(request.body)
    kit = SodimacKits.objects.create(
        kitnumber=body.get('kitnumber', ''),
        sku=body.get('sku', ''),
        quantity=int(body.get('quantity', 0)),
        ean=body.get('ean') or None,
    )
    return JsonResponse({'success': True, 'id': kit.id})


@login_required
def get_monthly_invoices(request):
    try:
        sigo = SigoConnection()
        sodi = ConnectionsSodimac()
        ocs = sigo.sync_siigo_to_db()
        costs = sodi.get_oc_costs(ocs)
        sigo.check_invoice_novelties(costo_por_oc=costs)
        return JsonResponse({'success': True, 'message': 'todo bien'}, status=200) 
    except Exception as e:
        print(e)
        return JsonResponse({'success': False, 'message': str(e)}, status=500)


def process_orders_and_create_in_shopify(sodi):
    """Procesa órdenes de Sodimac y las crea en Shopify."""
    data_log = {
        "error": False,
        "get_orders": False,
        "log": "No se encontraron ordenes.",
        "success_orders": [],
        "error_orders": [],
    }
    not_found_skus = []
    data_log["len_orders"] = 0
    resultado_1 = sodi.get_orders_api(tipo_orden="1")
    resultado_4 = sodi.get_orders_api(tipo_orden="4")
    if resultado_1 or resultado_4:
        print("Haciendo cruces de SKUS")
        sodi.make_merge()
        orders = sodi.get_orders()
        orders_generated = [
            int(i.id)
            for i in SodimacOrders.objects.filter(
                id__in=orders.ORDEN_COMPRA.unique()
            ).exclude(oc_shopify__icontains="No se encontro el SKU")
        ]
        orders = orders.loc[~orders["ORDEN_COMPRA"].isin(orders_generated)]
        if not orders.empty:
            shopi = ConnectionsShopify()
            shopi.set_orders_df(orders)
            shopi.get_variant_id()
            not_found_skus = shopi.get_not_found_skus()
            orders = shopi.get_orders()
            print(orders)
            print("creando ordenes")
            orders_created = shopi.create_orders()
            success_orders = orders_created["success"]
            error_orders = orders_created["error"]
            data_log["success_orders"] = success_orders
            data_log["error_orders"] = error_orders
            success_len = len(success_orders)
            error_len = len(error_orders)
            print("Se ejecuto shopy satisfactoriamente")
            descripcion_error = ""
            descripcion_success = ""
            if success_len > 0:
                descripcion_success = (
                    f'ordenes generadas: {", ".join([str(i) for i in success_orders])}'
                )
                print(
                    f'ordenes generadas: {", ".join([str(i) for i in success_orders])}'
                )
                print(f"se generaron {success_len} ordenes satisfactoriamente")
            if error_len > 0:
                data_log["error"] = True
                descripcion_error = f'se encontraron errores en las ordenes: {", ".join([str(i) for i in error_orders])}'
                print(
                    f'se encontraron errores en las ordenes: {", ".join([str(i) for i in error_orders])}'
                )
            data_log["get_orders"] = True
            data_log["log"] = descripcion_error + " " + descripcion_success
            data_log["len_orders"] = orders.shape[0]
        else:
            data_log["log"] = "No se encontraron nuevas ordenes."
            data_log["len_orders"] = 0
    return data_log, not_found_skus


def handle_invoices_and_billing():
    """Maneja la reinyección de OCs y creación de facturas."""
    orders = [
        i["id"] for i in SodimacOrders.objects.filter(status="1-PENDIENTE").values()
    ]
    sodi = ConnectionsSodimac()
    sodi.reinyectar_oc(orders)
    sodi.get_orders_api(tipo_orden="1")
    sodi.get_orders_api(tipo_orden="4")
    sodi.make_merge()
    sodi.set_kits()
    df = sodi.get_orders()
    invoices = df.loc[df["ESTADO_OC"] == "4-ESTADO FINAL"]
    invoices_values = pd.DataFrame(
        SodimacOrders.objects.filter(
            novelty__contains="The total payments must be equal to the total invoice. The total invoice calculated is ",
            factura__isnull=True,
        ).values()
    )
    if not invoices_values.empty:
        invoices_values["novelty"] = invoices_values["novelty"].apply(
            lambda x: x.replace(
                "The total payments must be equal to the total invoice. The total invoice calculated is ",
                "",
            )
        )
        invoices_values["id"] = invoices_values["id"].astype(int)
        invoices = invoices.merge(
            invoices_values, how="left", left_on="ORDEN_COMPRA", right_on="id"
        )
        invoices["novelty"].fillna("0", inplace=True)
    invoices.drop_duplicates(inplace=True)
    taxes = [{"id": 16104}, {"id": 13456}]
    conn_sigo = SigoConnection()
    id_invoices = [
        int(i.id)
        for i in SodimacOrders.objects.filter(
            id__in=invoices["ORDEN_COMPRA"].unique(), factura__isnull=True
        )
    ]
    print(
        [
            i.factura
            for i in SodimacOrders.objects.filter(
                id__in=invoices["ORDEN_COMPRA"].unique(), factura__isnull=True
            )
        ]
    )
    invoices = invoices.loc[invoices["ORDEN_COMPRA"].isin(id_invoices)]
    responses = conn_sigo.create_invoice(invoices, taxes)
    for i in responses:
        item = SodimacOrders.objects.get(id=i)
        if responses[i].status_code == 201:
            item.status = "4-ESTADO FINAL"
            item.factura = responses[i].json()["name"]
            item.date_invoice = datetime.date.today()
            item.novelty = ""
            item.value = responses[i].json()["total"]
        else:
            item.novelty = responses[i].json()["Errors"][0]["Message"]
            if (
                item.novelty
                == "The document already exists. This occurs if you are making duplicate requests simultaneously."
            ):
                print(f"La factura para la oc {i} ya esta creada")
            else:
                print(f"ocurrio un error con la factura {i}")
        item.save()


def send_notification_email(data_log, not_found_skus):
    """Envía un email de notificación con el resumen del proceso."""
    sender = EmailSender()
    subject = "Log  Ejecución Creacion Ordenes Sodimac - Shopify"

    # Generar listas HTML
    success_list = ""
    if data_log["success_orders"]:
        success_list = (
            "<ul>"
            + "".join(
                [f"<li>Orden {order}</li>" for order in data_log["success_orders"]]
            )
            + "</ul>"
        )
    else:
        success_list = "<p>No hay órdenes generadas.</p>"

    error_list = ""
    if not_found_skus:
        error_list = (
            "<h4><strong>Tipo de error: sku no encontrado en Shopify</strong></h4>"
            + "<ul>"
            + "".join(
                [
                    f"<li><strong>Orden: </strong> {order['ORDEN_COMPRA']} | <strong>SKU: </strong>{order['SKU']}</li>"
                    for order in not_found_skus
                ]
            )
            + "</ul>"
        )
    else:
        error_list = "<p>No hay órdenes fallidas.</p>"

    html_message = f"""
    <html>
    <body>
        <h2>Resumen de Ejecución del Bot Sodimac</h2>
        <p><strong>Fecha y Hora:</strong> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Órdenes Encontradas:</strong> {data_log['len_orders']}</p>
        <p><strong>Errores:</strong> {len(not_found_skus) + (len(data_log['error']) if data_log['error'] else 0) }</p>
        
        <h3>Órdenes Generadas Exitosamente</h3>
        {success_list}
        
        <h3>Órdenes con Errores</h3>
        {error_list}
    </body>
    </html>
    """
    recipient_list = NOTIFICATIONS_RECIPENTS
    try:
        sender.send_html_email(subject, html_message, recipient_list)
        print("Email de notificación enviado.")
    except Exception as e:
        print(f"Error enviando email: {e}")


def create_orders(request):
    try:
        print(
            f'*** debug inicia bot sodimac {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ***'
        )
        sodi = ConnectionsSodimac()
        data_log, not_found_skus = process_orders_and_create_in_shopify(sodi)
        print(
            f'*** debug termina bot sodimac {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***'
        )

        # Guardar log en BD
        log_item = LogBotOrders()
        log_item.get_orders = data_log["get_orders"]
        log_item.error = data_log["error"]
        log_item.log = data_log["log"]
        log_item.save()

        # Manejar facturas
        handle_invoices_and_billing()

        # Enviar notificación por email
        send_notification_email(data_log, not_found_skus)

        return redirect("pamo_bots:get_orders")
    except Exception as e:
        print(f"Error en create_orders: {e}")
        # Opcional: enviar email de error
        return redirect("pamo_bots:get_orders")


def set_inventory(request):
    # se recibe un archivo en excel, actualiza los registros que se encuentran en la base y los que no los crea
    if request.method == "GET":
        form = fileForm()
        data = {"form": form}
        return render(request, "sincronizacion_sodimac.html", context=data)
    elif request.method == "POST":
        # crea o actualiza los registros en la base de datos
        form_1 = fileForm(request.POST, request.FILES)
        if form_1.is_valid():
            file = request.FILES["file"]
            core = Core()
            core.set_df(file)
            core.process()
            products, df = core.get_products()
            sodi = ConnectionsSodimac()
            response_get = sodi.get_inventario([i.ean for i in products])
            save_review(response_get)
            df_resposne = pd.DataFrame(response_get)
            df_resposne = df_resposne.loc[df_resposne["success"] == True]
            df = df_resposne.merge(df, how="left", on="ean")
            # sodi.set_inventory(df)
            return JsonResponse({"success": True, "message": ""})
        else:
            print(form_1.errors)
            print(
                f'*** error en seteo de archivo actualizacion {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***'
            )


# def get_inventory_view(request):
#     if request.method == "POST":
#         data = json.loads(request.body)
#         ean_list = data.get("products")
#         sodi = ConnectionsSodimac()
#         return JsonResponse(sodi.get_inventario(ean_list)[0])


# def set_inventory_view(request):
#     if request.method == "POST":
#         data = json.loads(request.body)
#         sku = data.get("sku")
#         product = data.get("product")
#         stock = data.get("stock")
#         columnas = ["sku", "ean", "stock"]
#         data = [[sku, product, stock]]
#         df = pd.DataFrame(data, columns=columnas)
#         sodi = ConnectionsSodimac()
#         data = sodi.set_inventory(df)
#         core = Core()
#         core.update_database_item(sku, product, stock)
#         return JsonResponse(data)


def update_base(request):
    products = ProductsSodimac.objects.all()
    list_ean = [i.ean for i in products]
    sodi = ConnectionsSodimac()
    response = sodi.get_inventario(list_ean)
    save_review(response)
    return JsonResponse({"success": True, "message": ""})


@login_required
def download_products_excel(request):
    import io
    products = ProductsSodimac.objects.values('sku_sodimac', 'sku_pamo', 'ean')
    df = pd.DataFrame(list(products))
    output = io.BytesIO()
    df.to_excel(output, index=False, sheet_name='Productos Sodimac')
    output.seek(0)
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="productos_sodimac.xlsx"'
    return response


@login_required
def download_kits_excel(request):
    import io
    from quote_print.models import SodimacKits
    kits = SodimacKits.objects.values('kitnumber', 'ean', 'sku', 'quantity')
    df = pd.DataFrame(list(kits))
    output = io.BytesIO()
    df.to_excel(output, index=False, sheet_name='Kits Sodimac')
    output.seek(0)
    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="kits_sodimac.xlsx"'
    return response


def save_review(response):
    products = ProductsSodimac.objects.all()
    products = pd.DataFrame(products.values())
    df = pd.DataFrame(response)
    df = df.merge(products, how="left", on=["ean"])
    df = df[["sku_sodimac", "sku_pamo", "ean", "message"]]
    df.to_excel(os.path.join(settings.MEDIA_ROOT, "final_review.xlsx"), index=False)