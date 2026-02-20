from django.shortcuts import render, redirect
from django.conf import settings
from pamo.conecctions_shopify import ConnectionsShopify
from django.http import JsonResponse, HttpResponse
from pamo.constants import *
from pamo.queries import *
from datetime import timedelta, datetime
from django.contrib.auth.decorators import login_required
from quote_print.models import Quote
from pamo.functions import make_json
from pamo.connecctions_sigo import SigoConnection
from quote_print.models import SigoCostumers
import pandas as pd
import re
import json
from django.contrib.auth.decorators import login_required


@login_required
def list(request):
    try:
        code = request.GET.get('code')
    except:
        pass
    print(f'*** inicia lista cotizaciones {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    last_element = Quote.objects.latest('id')
    end_cursor = last_element.cursor
    ConnectionsShopify()
    shopify = ConnectionsShopify()
    response = shopify.request_graphql(GET_DRAFT_ORDERS.format( cursor= f",after:\"{end_cursor}\""))
    if response.json()['data']['draftOrders']['pageInfo']['endCursor'] != None:
        res  = response.json()['data']['draftOrders']['edges']
        cursor_new = response.json()['data']['draftOrders']['pageInfo']['endCursor']
        daft_orders = make_json(res)
        data_list =[]
        for i in daft_orders:
            if str(i['node']['name']) != last_element.name:
                dic = {}
                dic['id'] = i['node']['id'].replace('gid://shopify/DraftOrder/',"")
                dic['name'] = i['node']['name']
                dic['created_at'] = i['node']['createdAt']
                dic['total'] = int(float(i['node']['totalPrice']))
                try:
                    dic['nit'] = i['node']['customer']['addresses'][0]['company'].split('-')[0][:24]
                except:
                    dic['nit'] = None
                dic['seller'] = i['node']['tags']if i['node']['tags'] else None
                dic['seller'] = dic['seller'][0] if dic['seller'] else None
                nombre =  i['node']['customer']['firstName'].title() if (i['node']['customer']) and (i['node']['customer']['firstName']) else "" 
                apellido = i['node']['customer']['lastName'].title() if (i['node']['customer']) and (i['node']['customer']['lastName']) else ""     
                dic['customer'] = f"{nombre} {apellido}" 
                data_list.append(dic)
        dic['cursor'] = cursor_new
        data_to_save = [Quote(**elemento) for elemento in data_list]
        Quote.objects.bulk_create(data_to_save)
    quote_data = pd.DataFrame(Quote.objects.all().order_by('-id')[:500].values())
    # quote_data = pd.DataFrame([{'id':i.id, 'name':i.name, 'customer':i.customer, 'total':i.total, 'created_at':i.created_at} for i in data_table])
    sigo_costumers = pd.DataFrame(SigoCostumers.objects.all().values())
    merge_sigo = quote_data.merge(sigo_costumers, how = 'left', left_on='nit', right_on='identification', suffixes=('','_siigo'))
    merge_sigo.fillna('0', inplace=True)
    quote_data = merge_sigo.to_dict(orient='records')
    data = {"table" :quote_data, 'url_base':settings.BASE_URL}
    print(f'*** finaliza lista cotizaciones {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    return render(request, 'table_draft_orders.html', data)

def _get_draft_data(id):
    """Fetch and prepare draft order data from Shopify for the given quote id."""
    ConnectionsShopify()
    shopify = ConnectionsShopify()
    query = GET_DRAFT_ORDER.format(id)
    response = shopify.request_graphql(query)
    date_update = datetime.strptime(response.json()['data']['draftOrders']['edges'][0]['node']['updatedAt'][0:10], '%Y-%m-%d')
    plazo = (date_update + timedelta(days=10)).strftime('%d/%m/%Y')
    draft = response.json()['data']['draftOrders']['edges'][0]['node']
    try:
        draft['customer']['metafields']['edges'][0]['node']['value'] = ''
        draft['customer']['metafields']['edges'][1]['node']['value'] = ''
    except:
        pass
    try:
        res = re.search(r'\[(\d+)\]', [i['node']['value'] for i in draft['customer']['metafields']['edges'] if i['node']['key'] == 'numero_documento_identificaci_n'][0])
        num = res.group(1)
    except:
        num = None
    for i in draft['lineItems']['edges']:
        try:
            i['sku'] = i['node']['product']['variants']['edges'][0]['node']['sku']
            i['scr'] = i['node']['product']['images']['edges'][0]['node']['originalSrc']
        except:
            pass
        if str(i['node']['title']).__contains__('"'):
            i['node']['title'] = i['node']['title'].replace('"', '~')
        if str(i['node']['title']).__contains__("'"):
            i['node']['title'] = i['node']['title'].replace("'", '~')
    return {'info': draft, 'plazo': plazo, 'update': date_update.strftime('%d/%m/%Y'), 'nit': num,
            'url': f"https://api.whatsapp.com/send?phone={SALES_PHONE}&text=Hola,%20deseo%20revisar%20mi%20cotización%20{draft['name'][1]}",
            'quote_id': id}


@login_required
def print_drafr(request, id):
    print(f'*** inicia impresion de cotizacion {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    data = _get_draft_data(id)
    print(f'*** finaliza impresion de cotizacion {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    return render(request, 'print.html', data)

@login_required
def update_draft (request,id_sho):
    print(f'*** inicia actualizacion de cotizacion {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    print('esta entrando')
    ConnectionsShopify()
    shopify = ConnectionsShopify()
    query = GET_DRAFT_ORDER_UPDATE.format(id_sho)
    print(query)
    response = shopify.request_graphql(query)
    print(response.json())
    res = response.json()['data']['draftOrders']['edges'][0]
    total = int(float(res['node']['totalPrice']))
    nombre =  res['node']['customer']['firstName'].title() if (res['node']['customer']) and (res['node']['customer']['firstName']) else "" 
    apellido = res['node']['customer']['lastName'].title() if (res['node']['customer']) and (res['node']['customer']['lastName']) else ""     
    customer = f"{nombre} {apellido}" 
    quote = Quote.objects.get(id=id_sho)
    quote.customer = customer
    quote.total = total
    quote.nit = res['node']['customer']['addresses'][0]['company'].split('-')[0][:24] if (res['node']['customer']) and ('addresses' in res['node']['customer']) and (res['node']['customer']['addresses'][0]['company']) else None
    seller = res['node']['tags']if res['node']['tags'] else None
    quote.seller = seller[0] if seller else None

    quote.save()
    print(f'*** inicia actualizacion de cotizacion {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}***')
    return JsonResponse({'success':True, 'message': ''})

@login_required
def set_all_constumers(request):
    try:
        sigo_con = SigoConnection()
        sigo_con.synchronize_all_costumers()
        return JsonResponse({'success':True, 'message': ''})
    except Exception as e:
        print(e)
        return JsonResponse({'success':False, 'message': f'No se completó la carga {str(e)}'})

@login_required
def search_new_customers(request):
    try:
        sigo_con = SigoConnection()
        customer_created = sigo_con.synchronize_new_costumer()
        return JsonResponse({'success':True, 'message': f'clientes encontrados: {customer_created}'})
    except Exception as e:
        print(e)
        return JsonResponse({'success':False, 'message': f'No se completó la carga {str(e)}'})

@login_required
def get_info_customer(request, id_siigo):
    try:
        sigo_con = SigoConnection()
        data = sigo_con.get_info_costumer(id_siigo)
        return JsonResponse({'success':True, 'data': json.dumps(data)})
    except Exception as e:
        print(e)
        return JsonResponse({'success':False, 'message': f'No se completó la carga {str(e)}'})


@login_required
def generate_pdf(request, id):
    from playwright.sync_api import sync_playwright
    from django.template.loader import render_to_string

    data = _get_draft_data(id)
    # Render the template to an HTML string — no HTTP request needed
    html_content = render_to_string('print.html', data, request=request)
    # Inject <base> tag so Playwright resolves /static/... URLs correctly
    base_url = request.build_absolute_uri('/')
    html_content = html_content.replace('<head>', f'<head><base href="{base_url}">', 1)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        # domcontentloaded is instant (just HTML parsed, no waiting for every image)
        # networkidle then waits for CSS/JS/images to finish (500ms of inactivity)
        page.set_content(html_content, wait_until='domcontentloaded', timeout=10000)
        page.wait_for_load_state('networkidle', timeout=30000)
        pdf_bytes = page.pdf(
            format='A4',
            print_background=True,
            margin={'top': '0mm', 'bottom': '0mm', 'left': '0mm', 'right': '0mm'}
        )
        browser.close()

    quote_name = Quote.objects.filter(id=id).values_list('name', flat=True).first() or str(id)
    filename = f"cotizacion_{quote_name.lstrip('#')}.pdf"

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response