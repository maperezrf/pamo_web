"""
ReportLab PDF generator for cotizaciones.
Positions are in points (pt). A4 = 595.27 x 841.89 pt.
ReportLab origin is bottom-left corner.

Tweak the LAYOUT constants below if any element needs adjustment.
"""
import io
import os
import requests

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg
from django.conf import settings
from pamo.constants import SALES_PHONE

PAGE_W, PAGE_H = A4  # 595.27 x 841.89

# ── Layout constants (adjust if anything looks off) ──────────────────────────
Y_COMPANY_TOP  = 778   # y of first company info line (top-right block)
Y_CUSTOMER_TOP = 695   # y of first customer info line
Y_TABLE_FIRST  = 618   # y of table-header bottom on page with customer info
Y_TABLE_EXTRA  = 760   # y of table-header bottom on continuation pages
ROW_H          = 55    # height of each product row
HEADER_H       = 20    # height of the table header row

LEFT_X         = 22    # left edge of all content
RIGHT_X        = 574   # right edge of all content
CUSTOMER_VAL_X = 175   # x where customer field values start
TABLE_LEFT_X   = LEFT_X + 33  # left edge of product table (aligned with customer data)

# Column widths in pt — must sum to (RIGHT_X - TABLE_LEFT_X) = 519
COLS = [52, 68, 182, 52, 90, 75]   # FOTO  SKU  DESC  CANT  P.UNIT  TOTAL
assert sum(COLS) == RIGHT_X - TABLE_LEFT_X, f"COLS sum {sum(COLS)} != {RIGHT_X - TABLE_LEFT_X}"

# ── Footer / totals overflow constants ───────────────────────────────────────
FOOTER_BOTTOM   = 30    # pt from bottom edge: footer block starts here
FOOTER_GAP      = 10    # pt gap between footer separator line and footer content
TOTALS_H_EST    = 180   # conservative estimated height of the totals block (without footer)
# ─────────────────────────────────────────────────────────────────────────────


def _img_path(name):
    return os.path.join(settings.STATIC_ROOT, 'images', 'cotizacion_img', name)


def _fetch_remote_img(url, timeout=5):
    """Download a remote image and return an ImageReader, or None on failure."""
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return ImageReader(io.BytesIO(r.content))
    except Exception:
        return None


def _fmt_cop(value):
    """Format value as Colombian pesos: $ 1.234.567"""
    try:
        return "$ {:,.0f}".format(round(float(value))).replace(',', '.')
    except Exception:
        return str(value)


def _wrap_text(text, max_chars=36):
    """Simple word-wrap: returns list of lines."""
    words, lines, cur = text.split(), [], ''
    for w in words:
        if len(cur) + len(w) + 1 <= max_chars:
            cur = (cur + ' ' + w).strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _text(c, x, y, text, size=7.5, bold=False, color=colors.black):
    c.setFillColor(color)
    c.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
    c.drawString(x, y, str(text))


def _text_right(c, x, y, text, size=7.5, bold=False, color=colors.black):
    c.setFillColor(color)
    c.setFont('Helvetica-Bold' if bold else 'Helvetica', size)
    c.drawRightString(x, y, str(text))


def create_pdf(data):
    """
    Build the cotización PDF and return bytes.
    `data` is the same dict passed to the print.html template.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    draft    = data['info']
    plazo    = data['plazo']
    date_str = data['update']
    nit      = data['nit']
    items    = draft['lineItems']['edges']

    # ── Totals ───────────────────────────────────────────────────────────────
    total     = float(draft['totalPrice'])
    subtotal  = total / 1.19
    iva       = subtotal * 0.19
    bruto     = sum(
        float(i['node']['originalUnitPrice']) * int(i['node']['quantity'])
        for i in items
    ) / 1.19
    descuento    = bruto - subtotal
    has_discount = bool(draft.get('appliedDiscount')) and descuento > 1
    pct_desc     = round((descuento / bruto) * 100) if bruto > 0 else 0

    # ── Pre-load footer image height for overflow threshold ───────────────────
    _HELP_W = int((RIGHT_X - TABLE_LEFT_X) * 0.58)
    _help_h_est = 85
    try:
        _hr = ImageReader(_img_path('help.jpeg'))
        _hw, _hh = _hr.getSize()
        _help_h_est = _hh * (_HELP_W / _hw)
    except Exception:
        pass
    # totals must end above the footer separator line (+ 5pt margin)
    FOOTER_TOP_THRESHOLD = FOOTER_BOTTOM + _help_h_est + FOOTER_GAP + 5

    # Split items into pages of 7
    groups = [items[i:i + 7] for i in range(0, max(len(items), 1), 7)]

    # ── Helper: draw company info block (reused on every content page) ────────
    def _draw_company_info():
        company_lines = [
            ('FEPRIN SAS / PAMO.CO',                                      False),
            ('NIT: 900.382.733-3  Régimen Común',                         False),
            ('Actividad Económica 4752  Tarifa Renta 0,40%',              False),
            ('BOGOTA - COLOMBIA',                                          False),
            ('',                                                           False),
            ('No somos Autoretenedores - No somos Grandes Contribuyentes', False),
            ('Régimen IVA: COMÚN  Actividad ICA: 47521  6,90x mil',      False),
        ]
        y = Y_COMPANY_TOP
        gray = colors.HexColor('#555555')
        for line, bold in company_lines:
            if line:
                _text_right(c, RIGHT_X, y, line, size=7, bold=bold, color=gray)
            y -= 9.5
        c.setFillColor(colors.black)

    # ── Page 1 – Cover ───────────────────────────────────────────────────────
    c.setFillColor(colors.white)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.drawImage(_img_path('Pg1.png'), 0, 0, width=PAGE_W, height=PAGE_H, mask='auto')
    c.showPage()

    # ── Page 2 – ¿Por qué Pamo? ──────────────────────────────────────────────
    c.setFillColor(colors.white)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.drawImage(_img_path('Pg2.png'), 0, 0, width=PAGE_W, height=PAGE_H, mask='auto')
    c.showPage()

    # ── Content pages ────────────────────────────────────────────────────────
    # y_row persists after the loop to calculate sep_y for the totals block
    y_row = Y_TABLE_FIRST

    for page_idx, group in enumerate(groups):
        is_first = page_idx == 0
        is_last  = page_idx == len(groups) - 1

        c.setFillColor(colors.white)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        # Página 1 de contenido → Pg3.png; resto → Hoja-con-cintillo.png
        bg = 'Pg3.png' if is_first else 'Hoja-con-cintillo.png'
        c.drawImage(_img_path(bg), 0, 0, width=PAGE_W, height=PAGE_H, mask='auto')

        # ── Company info block (solo en Pg3, no en Hoja-con-cintillo) ──────
        if is_first:
            _draw_company_info()

        # ── Customer info (first page only) ───────────────────────────────
        if is_first:
            customer = draft.get('customer') or {}
            y = Y_CUSTOMER_TOP

            def cust_field(label, value, y_pos):
                _text(c, LEFT_X + 33, y_pos, label, size=8, bold=True)
                _text(c, CUSTOMER_VAL_X, y_pos, value, size=8)
                return y_pos - 14

            if customer.get('displayName'):
                y = cust_field('Nombre / Empresa:', customer['displayName'].title(), y)
            if customer.get('email'):
                y = cust_field('Correo:', customer['email'], y)
            if nit:
                y = cust_field('Nit:', str(nit), y)
            phone = (customer.get('defaultAddress') or {}).get('phone', '')
            if phone:
                y = cust_field('Teléfono:', phone.replace("+57", ""), y)
            _text(c, LEFT_X + 33, y, f'Plazo: 10 días   Fecha de Vencimiento: {plazo}', size=8)
            _text_right(c, RIGHT_X, Y_CUSTOMER_TOP, f'Fecha:  {" / ".join(date_str.split("/"))} /', size=8)
            quote_num = draft['name'][1:]
            num_w = c.stringWidth(quote_num, 'Helvetica', 8)
            _text_right(c, RIGHT_X,         Y_CUSTOMER_TOP - 14, quote_num,         size=8, color=colors.red)
            _text_right(c, RIGHT_X - num_w, Y_CUSTOMER_TOP - 14, 'Cotización No. ', size=8)

        # ── Product table ─────────────────────────────────────────────────
        table_top = Y_TABLE_FIRST if is_first else Y_TABLE_EXTRA

        # Header background
        c.setFillColor(colors.HexColor("#f5f3f3"))
        c.rect(TABLE_LEFT_X, table_top, RIGHT_X - TABLE_LEFT_X, HEADER_H, fill=1, stroke=0)
        c.setFillColor(colors.black)

        # Header labels
        headers = ['FOTO', 'SKU', 'DESCRIPCIÓN', 'CANTIDAD', 'P. UNITARIO', 'TOTAL']
        xh = TABLE_LEFT_X
        for h, w in zip(headers, COLS):
            _text(c, xh + 3, table_top + 6, h, size=6.5, bold=True)
            xh += w

        # Product rows
        y_row = table_top
        for item in group:
            y_row -= ROW_H
            node  = item['node']
            x     = TABLE_LEFT_X

            # — Photo
            img_url = item.get('scr')
            if img_url:
                img_reader = _fetch_remote_img(img_url)
                if img_reader:
                    try:
                        c.drawImage(img_reader, x + 2, y_row + 3,
                                    width=COLS[0] - 4, height=ROW_H - 6,
                                    preserveAspectRatio=True, mask='auto')
                    except Exception:
                        pass
            x += COLS[0]

            # — SKU (máx 14 caracteres)
            _text(c, x + 3, y_row + ROW_H - 13, item.get('sku', '')[:14], size=7)
            x += COLS[1]

            # — Description (word-wrap, max 3 lines)
            title = node.get('title', '').replace('~', '"')
            for ln_i, ln in enumerate(_wrap_text(title, 34)[:3]):
                _text(c, x + 3, y_row + ROW_H - 13 - ln_i * 9, ln, size=7)
            x += COLS[2]

            # — Quantity
            _text(c, x + 3, y_row + ROW_H - 13, str(node.get('quantity', '')), size=7)
            x += COLS[3]

            # — Unit price (ex IVA)
            unit = float(node.get('originalUnitPrice', 0)) / 1.19
            _text(c, x + 3, y_row + ROW_H - 13, _fmt_cop(unit), size=7)
            x += COLS[4]

            # — Total line
            _text(c, x + 3, y_row + ROW_H - 13, _fmt_cop(unit * int(node.get('quantity', 0))), size=7)

            # Row separator
            c.setStrokeColor(colors.HexColor('#cccccc'))
            c.line(TABLE_LEFT_X, y_row, RIGHT_X, y_row)
            c.setStrokeColor(colors.black)

        # Solo cerrar la página si NO es la última — la última queda abierta para los totales
        if not is_last:
            c.showPage()

    # ── Totals block ─────────────────────────────────────────────────────────
    # sep_y usa y_row del último grupo (persiste del loop)
    sep_y = y_row - 12

    # Si los totales no caben entre los productos y el pie de página → nueva página
    if sep_y - TOTALS_H_EST < FOOTER_TOP_THRESHOLD:
        c.showPage()
        c.setFillColor(colors.white)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        c.drawImage(_img_path('Hoja-con-cintillo.png'), 0, 0, width=PAGE_W, height=PAGE_H, mask='auto')
        sep_y = Y_TABLE_EXTRA - 20

    # Línea separadora sobre los totales
    c.setStrokeColor(colors.HexColor('#aaaaaa'))
    c.line(TABLE_LEFT_X, sep_y, RIGHT_X, sep_y)
    c.setStrokeColor(colors.black)

    # — Información de pago (columna izquierda)
    py = sep_y - 14
    _text(c, TABLE_LEFT_X, py,
          'Realizar el pago a nombre de FEPRIN SAS, NIT 900382733.',
          size=7, bold=True)
    py -= 11
    _text(c, TABLE_LEFT_X, py,
          'Bancolombia Cuenta de Ahorros No. 174-000021-78', size=7)

    # — Totales (columna derecha)
    label_x = RIGHT_X - 155
    ty = sep_y - 14

    def total_row(label, value, y_pos, bold_val=False):
        _text(c, label_x, y_pos, label, size=7.5, bold=True)
        _text_right(c, RIGHT_X, y_pos, value, size=7.5, bold=bold_val)
        return y_pos - 12

    ty = total_row('Total bruto', _fmt_cop(bruto), ty)
    if has_discount:
        ty = total_row(f'Descuento {pct_desc}%', _fmt_cop(descuento), ty)
    ty = total_row('Subtotal', _fmt_cop(subtotal), ty)
    ty = total_row('IVA', _fmt_cop(iva), ty)
    ty = total_row('Total', _fmt_cop(total), ty, bold_val=True)

    ICON_GAP = 10
    totals_w = RIGHT_X - label_x

    # — Botón pagar
    pago_h = 28
    try:
        pago_reader = ImageReader(_img_path('Bot-pago.png'))
        nat_w, nat_h = pago_reader.getSize()
        pago_h = nat_h * (totals_w / nat_w)
        pago_y = ty - pago_h - 8
        c.drawImage(pago_reader, label_x, pago_y,
                    width=totals_w, height=pago_h, mask='auto')
        c.linkURL(draft.get('invoiceUrl', ''),
                  (label_x, pago_y, RIGHT_X, pago_y + pago_h), thickness=0)
    except Exception:
        pago_y = ty - pago_h - 8

    # — Botones de descarga (certificación y RUT)
    dl_y = py - pago_h - 8
    lx = TABLE_LEFT_X
    for img_name, url in [
        ('certificacion.png', 'https://cdn.shopify.com/s/files/1/0617/8507/9974/files/Certificado_Bancolombia_Feprin_2026.pdf?v=1774303817'),
        ('rut.png',           'https://cdn.shopify.com/s/files/1/0617/8507/9974/files/RUT_FEPRIN_2026.pdf?v=1774303720'),
    ]:
        try:
            reader = ImageReader(_img_path(img_name))
            nat_w, nat_h = reader.getSize()
            iw = nat_w * (pago_h / nat_h)
            c.drawImage(reader, lx, dl_y, width=iw, height=pago_h, mask='auto')
            c.linkURL(url, (lx, dl_y, lx + iw, dl_y + pago_h), thickness=0)
            lx += iw + ICON_GAP
        except Exception:
            pass

    # — Banner Bre-B
    links_y = min(dl_y, pago_y)
    try:
        breb_reader = ImageReader(_img_path('bre-b.png'))
        breb_nat_w, breb_nat_h = breb_reader.getSize()
        breb_w = RIGHT_X - TABLE_LEFT_X
        breb_h = breb_nat_h * (breb_w / breb_nat_w)
        breb_y = links_y - breb_h - 10
        c.drawImage(breb_reader, TABLE_LEFT_X, breb_y,
                    width=breb_w, height=breb_h, mask='auto')
        js = "app.setClipboardContents('0091439530'); app.alert('Llave copiada: 0091439530', 3);"
        c.linkURL(f'javascript:{js}',
                  (TABLE_LEFT_X, breb_y, RIGHT_X, breb_y + breb_h),
                  thickness=0)
    except Exception:
        pass

    # ── Pie de página — siempre anclado al fondo de la última hoja ───────────
    HELP_W      = int((RIGHT_X - TABLE_LEFT_X) * 0.58)
    COL_GAP     = 10
    BTN_H       = 20
    text_x      = TABLE_LEFT_X + HELP_W + COL_GAP
    # Cargar imagen help para calcular altura real
    help_h = 85
    help_reader = None
    try:
        help_reader = ImageReader(_img_path('help.jpeg'))
        help_nat_w, help_nat_h = help_reader.getSize()
        help_h = help_nat_h * (HELP_W / help_nat_w)
    except Exception:
        pass

    # Imagen anclada desde FOOTER_BOTTOM hacia arriba
    help_y   = FOOTER_BOTTOM
    help_top = help_y + help_h

    # Línea separadora sobre el pie de página
    footer_sep_y = help_top + FOOTER_GAP
    c.setStrokeColor(colors.HexColor('#aaaaaa'))
    c.line(TABLE_LEFT_X, footer_sep_y, RIGHT_X, footer_sep_y)
    c.setStrokeColor(colors.black)

    # — Imagen "¿Necesitas ayuda?"
    if help_reader:
        c.drawImage(help_reader, TABLE_LEFT_X, help_y,
                    width=HELP_W, height=help_h, mask='auto')

    # — Botones WhatsApp y Teléfono superpuestos en la imagen
    empty_h = help_h * 0.45
    btn_y   = help_y + (empty_h - BTN_H) / 2
    BTN_GAP = 8
    wp_w, wp_drawing_ready = 0, None
    tel_w, tel_reader_ready = 0, None

    try:
        wp_drawing = svg2rlg(_img_path('wp.svg'))
        if wp_drawing:
            scale = BTN_H / wp_drawing.height
            wp_w  = wp_drawing.width * scale
            wp_drawing.width     = wp_w
            wp_drawing.height    = BTN_H
            wp_drawing.transform = (scale, 0, 0, scale, 0, 0)
            wp_drawing_ready = wp_drawing
    except Exception:
        pass

    try:
        tel_reader = ImageReader(_img_path('telefono.png'))
        tel_nat_w, tel_nat_h = tel_reader.getSize()
        tel_w = tel_nat_w * (BTN_H / tel_nat_h)
        tel_reader_ready = tel_reader
    except Exception:
        pass

    start_x = 157

    if wp_drawing_ready:
        renderPDF.draw(wp_drawing_ready, c, start_x, btn_y)
        c.linkURL(data.get('url', ''),
                  (start_x, btn_y, start_x + wp_w, btn_y + BTN_H), thickness=0)
    if tel_reader_ready:
        tel_x = start_x + wp_w + (BTN_GAP if wp_w else 0)
        c.drawImage(tel_reader_ready, tel_x, btn_y,
                    width=tel_w, height=BTN_H, mask='auto')
        c.linkURL(f'tel:{SALES_PHONE}',
                  (tel_x, btn_y, tel_x + tel_w, btn_y + BTN_H), thickness=0)

    # — Texto políticas (columna derecha, alineado con el tope de la imagen)
    pol_y = help_top - 5
    _text(c, text_x, pol_y,
          'POLÍTICAS DE REEMBOLSO DE FEPRIN SAS', size=7, bold=True)
    pol_y -= 8
    _text(c, text_x, pol_y, 'Consulta nuestra politica de reembolso en:', size=7)
    pol_y -= 7
    _text(c, text_x, pol_y, 'https://www.pamo.co/policies/refund-policy', size=7,
          color=colors.HexColor('#1155CC'))
    pol_y -= 8
    policy_lines = [
        '',
        '*Todas las devoluciones y/o garantías estarán sujetas al derecho',
        'de retracto y a la política de garantías.',
        '',
        '*Toda solicitud debe notificarse a ventas@pamo.co dentro de 30',
        'días calendario desde la recepción del producto.',
        '',
        '*Si la garantía es procedente, se realizará la reparación gratuita.',
        'El producto debe venir correctamente embalado.',
    ]
    for ln in policy_lines:
        if ln:
            _text(c, text_x, pol_y, ln, size=7,
                  color=colors.HexColor('#333333'))
        pol_y -= 8

    c.showPage()

    c.save()
    buf.seek(0)
    return buf.read()
