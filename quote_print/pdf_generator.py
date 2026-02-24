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
from django.conf import settings

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

# Column widths in pt — must sum to (RIGHT_X - LEFT_X) = 552
COLS = [52, 68, 215, 52, 90, 75]   # FOTO  SKU  DESC  CANT  P.UNIT  TOTAL
assert sum(COLS) == RIGHT_X - LEFT_X, f"COLS sum {sum(COLS)} != {RIGHT_X - LEFT_X}"
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

    # Split items into pages of 7
    groups = [items[i:i + 7] for i in range(0, max(len(items), 1), 7)]

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
    for page_idx, group in enumerate(groups):
        is_first = page_idx == 0
        is_last  = page_idx == len(groups) - 1

        c.setFillColor(colors.white)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        c.drawImage(_img_path('Pg3.png'), 0, 0, width=PAGE_W, height=PAGE_H, mask='auto')

        # ── Company info block (top-right, right-aligned) ─────────────────
        company_lines = [
            ('FEPRIN SAS / PAMO.CO',                                     True),
            ('NIT: 900.382.733-3  Régimen Común',                       False),
            ('Actividad Económica 4752  Tarifa Renta 0,40%',            False),
            ('Teléfonos: (601)9168880  6019179988',                     False),
            ('',                                                         False),
            ('No somos Autoretenedores - No somos Grandes Contribuyentes', False),
            ('Régimen IVA: COMÚN  Actividad ICA: 47521  6,90x mil',    False),
        ]
        y = Y_COMPANY_TOP
        gray = colors.HexColor('#555555')
        for line, bold in company_lines:
            if line:
                _text_right(c, RIGHT_X, y, line, size=7, bold=bold, color=gray)
            y -= 9.5
        c.setFillColor(colors.black)

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
                y = cust_field('Teléfono:', phone, y)
            _text(c, LEFT_X + 33, y, f'Plazo: 10 días   Fecha de Vencimiento: {plazo}', size=8)
            y -= 14
            _text(c, LEFT_X + 33, y, 'Teléfono: 316 7578855', size=8)

            # Right side: date and quote number
            _text_right(c, RIGHT_X, Y_CUSTOMER_TOP,      f'Fecha: {date_str}', size=8)
            _text_right(c, RIGHT_X, Y_CUSTOMER_TOP - 14, f"Cotización No. {draft['name'][1:]}", size=8)

        # ── Product table ─────────────────────────────────────────────────
        table_top = Y_TABLE_FIRST if is_first else Y_TABLE_EXTRA

        # Header background
        c.setFillColor(colors.HexColor('#d1d1d1'))
        c.rect(LEFT_X, table_top, RIGHT_X - LEFT_X, HEADER_H, fill=1, stroke=0)
        c.setFillColor(colors.black)

        # Header labels
        headers = ['FOTO', 'SKU', 'DESCRIPCIÓN', 'CANTIDAD', 'P. UNITARIO', 'TOTAL']
        xh = LEFT_X
        for h, w in zip(headers, COLS):
            _text(c, xh + 3, table_top + 6, h, size=6.5, bold=True)
            xh += w

        # Product rows
        y_row = table_top
        for item in group:
            y_row -= ROW_H
            node  = item['node']
            x     = LEFT_X

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

            # — SKU
            _text(c, x + 3, y_row + ROW_H - 13, item.get('sku', ''), size=7)
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
            c.line(LEFT_X, y_row, RIGHT_X, y_row)
            c.setStrokeColor(colors.black)

        # ── Totals + footer (last page only) ─────────────────────────────
        if is_last:
            sep_y = y_row - 12
            c.setStrokeColor(colors.HexColor('#aaaaaa'))
            c.line(LEFT_X, sep_y, RIGHT_X, sep_y)
            c.setStrokeColor(colors.black)

            # — Payment info (bottom-left)
            py = sep_y - 14
            _text(c, LEFT_X, py,
                  'Realizar el pago a nombre de FEPRIN SAS, NIT 900382733.',
                  size=7, bold=True)
            py -= 11
            _text(c, LEFT_X, py,
                  'Bancolombia Cuenta de Ahorros No. 174-000021-78', size=7)

            # — Totals (bottom-right)
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
            total_row('Total', _fmt_cop(total), ty, bold_val=True)

            # — Policies
            pol_y = py - 20
            c.setStrokeColor(colors.HexColor('#aaaaaa'))
            c.line(LEFT_X, pol_y + 8, RIGHT_X, pol_y + 8)
            c.setStrokeColor(colors.black)

            pol_y -= 4
            _text(c, LEFT_X, pol_y,
                  'POLÍTICAS DE REEMBOLSO DE FEPRIN SAS', size=6.5, bold=True)
            pol_y -= 8
            _text(c, LEFT_X, pol_y,
                  'Consulta: https://www.pamo.co/policies/refund-policy', size=6)
            pol_y -= 8
            policy = (
                'Todas las devoluciones y/o garantías estarán sujetas al derecho de retracto '
                'y a la política de garantías. Toda solicitud debe notificarse a ventas@pamo.co '
                'dentro de 30 días calendario desde la recepción del producto. Si la garantía es '
                'procedente, se realizará la reparación gratuita. El producto debe venir '
                'correctamente embalado, limpio y desinfectado. CONSERVE EL EMPAQUE Y GUÍAS.'
            )
            for ln in _wrap_text(policy, 110)[:3]:
                _text(c, LEFT_X, pol_y, ln, size=5.5,
                      color=colors.HexColor('#333333'))
                pol_y -= 7

        c.showPage()

    c.save()
    buf.seek(0)
    return buf.read()
