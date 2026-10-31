"""
Raj & Sons Wholesale Gift House - Automated Category-Wise PDF Catalog Generator

Usage:
    python generate_catalog.py                      # interactive category menu
    python generate_catalog.py --category Crockery  # one category
    python generate_catalog.py --all                # every category, one PDF each
Optional: --excel, --images, --out, --phone
"""
import argparse
import io
import os
import re
import sys

import pandas as pd
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (Image, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)
from xml.sax.saxutils import escape

# ---------------- Settings (edit here) ----------------
BUSINESS_NAME = "Raj & Sons Wholesale Gift House, Basti"
TAGLINE = "Direct Wholesale Rates \u2022 Safe All-India Courier Delivery"
PHONE = "+91-XXXXXXXXXX"          # <-- put the real WhatsApp number here
MAROON = colors.HexColor("#7A0C0C")
GOLD = colors.HexColor("#B8860B")
PRICE_RED = colors.HexColor("#B81414")

PAGE_W, PAGE_H = A4
SIDE_MARGIN = 30
TOP_MARGIN = 105     # room for the header drawn on every page
BOTTOM_MARGIN = 45
COLS = 2
ROWS_PER_PAGE = 3    # 2 x 3 = 6 products per page
FRAME_PAD = 12      # ReportLab frames add 6pt padding top and bottom
ROW_HEIGHT = (PAGE_H - TOP_MARGIN - BOTTOM_MARGIN - FRAME_PAD) / ROWS_PER_PAGE - 1
IMG_BOX = 120        # product image box, points
IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".JPG", ".JPEG", ".PNG")

# Accepted header spellings -> standard name (compared lowercase, spaces removed)
ALIASES = {
    "category": "Category",
    "itemcode": "Item Code", "code": "Item Code", "sku": "Item Code",
    "itemname": "Item Name", "name": "Item Name", "productname": "Item Name",
    "rate": "Rate", "price": "Rate", "wholesalerate": "Rate",
    "description": "Description", "details": "Description",
    "imagefile": "Image File", "imagename": "Image File", "image": "Image File",
}


# ---------------- Page numbering + header on every page ----------------
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            self._draw_footer(total)
            super().showPage()
        super().save()

    def _draw_footer(self, total):
        self.saveState()
        self.setStrokeColor(colors.HexColor("#CCCCCC"))
        self.line(SIDE_MARGIN, 34, PAGE_W - SIDE_MARGIN, 34)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#555555"))
        self.drawString(SIDE_MARGIN, 22, f"For Orders & Inquiries: WhatsApp {PHONE}")
        self.drawRightString(PAGE_W - SIDE_MARGIN, 22,
                             f"Page {self._pageNumber} of {total}")
        self.restoreState()


def make_header(category_title, logo_path):
    def draw(c, doc):
        c.saveState()
        x_text = PAGE_W / 2
        if logo_path and os.path.exists(logo_path):
            try:
                c.drawImage(logo_path, SIDE_MARGIN, PAGE_H - 70, width=48,
                            height=48, preserveAspectRatio=True, mask="auto")
            except Exception:
                pass
        c.setFillColor(MAROON)
        c.setFont("Helvetica-Bold", 17)
        c.drawCentredString(x_text, PAGE_H - 40, BUSINESS_NAME)
        c.setFillColor(colors.HexColor("#444444"))
        c.setFont("Helvetica-Oblique", 9)
        c.drawCentredString(x_text, PAGE_H - 55, TAGLINE)
        c.setFillColor(GOLD)
        c.rect(SIDE_MARGIN, PAGE_H - 92, PAGE_W - 2 * SIDE_MARGIN, 20,
               stroke=0, fill=1)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 11)
        c.drawCentredString(x_text, PAGE_H - 86, f"CATEGORY: {category_title.upper()}")
        c.restoreState()
    return draw


# ---------------- Data helpers ----------------
def load_data(excel_path):
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"Excel file not found: {excel_path}")
    df = pd.read_excel(excel_path, dtype=str)
    rename = {}
    for col in df.columns:
        key = re.sub(r"\s+", "", str(col)).lower()
        if key in ALIASES:
            rename[col] = ALIASES[key]
    df = df.rename(columns=rename)
    if "Category" not in df.columns:
        raise ValueError("Excel must have a 'Category' column. Found: "
                         + ", ".join(map(str, df.columns)))
    for col in ("Item Code", "Item Name", "Rate", "Description", "Image File"):
        if col not in df.columns:
            df[col] = ""
    df = df.fillna("")
    df["_cat_key"] = df["Category"].astype(str).str.strip().str.lower()
    return df


def list_categories(df):
    seen, out = set(), []
    for orig, key in zip(df["Category"], df["_cat_key"]):
        if key and key not in seen:
            seen.add(key)
            out.append(str(orig).strip())
    return out


def format_rate(value):
    s = str(value).strip()
    if not s or s.lower() in ("nan", "none"):
        return "On Request"
    cleaned = re.sub(r"(?i)(rs\.?|inr|\u20b9|/-|,|\s)", "", s)
    try:
        num = float(cleaned)
        return f"Rs. {int(num)}/-" if num == int(num) else f"Rs. {num:.2f}/-"
    except ValueError:
        return s


def find_image(images_dir, filename, item_code):
    """Return a real path or None. Tries filename, case-insensitive match,
    then Item Code + common extensions."""
    if not os.path.isdir(images_dir):
        return None
    files = {f.lower(): f for f in os.listdir(images_dir)}
    fn = str(filename).strip()
    if fn:
        p = os.path.join(images_dir, fn)
        if os.path.isfile(p):
            return p
        if fn.lower() in files:
            return os.path.join(images_dir, files[fn.lower()])
    code = str(item_code).strip()
    if code:
        for ext in IMG_EXTS:
            if (code + ext).lower() in files:
                return os.path.join(images_dir, files[(code + ext).lower()])
    return None


def compressed_image(path, keep):
    """Shrink to ~400px JPEG so 100-item PDFs stay small. Returns Image flowable."""
    try:
        with PILImage.open(path) as im:
            if im.mode in ("RGBA", "LA", "P"):
                im = im.convert("RGBA")
                bg = PILImage.new("RGB", im.size, "white")
                bg.paste(im, mask=im.split()[-1])
                im = bg
            else:
                im = im.convert("RGB")
            im.thumbnail((400, 400))
            buf = io.BytesIO()
            im.save(buf, "JPEG", quality=78, optimize=True)
        buf.seek(0)
        keep.append(buf)
        w, h = im.size
        scale = min(IMG_BOX / w, IMG_BOX / h)
        return Image(buf, width=w * scale, height=h * scale)
    except Exception:
        return None


def placeholder(styles_):
    t = Table([[Paragraph("Image Coming Soon", styles_["ph"])]],
              colWidths=[IMG_BOX], rowHeights=[IMG_BOX])
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#BBBBBB")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0F0F0")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def make_styles():
    base = getSampleStyleSheet()["Normal"]

    def s(name, **kw):
        return ParagraphStyle(name, parent=base, alignment=1, **kw)
    return {
        "title": s("t", fontName="Helvetica-Bold", fontSize=10, leading=12),
        "code": s("c", fontName="Helvetica", fontSize=9, leading=11,
                  textColor=colors.HexColor("#444444")),
        "price": s("p", fontName="Helvetica-Bold", fontSize=11, leading=14,
                   textColor=PRICE_RED),
        "desc": s("d", fontName="Helvetica", fontSize=8, leading=10,
                  textColor=colors.HexColor("#555555")),
        "ph": s("ph", fontName="Helvetica-Oblique", fontSize=9,
                textColor=colors.HexColor("#888888")),
    }


def trunc(text, n):
    text = str(text).strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "\u2026"


# ---------------- Main builder ----------------
def build_catalog(excel_path, images_dir, category, output_pdf,
                  logo_path="assets/logo.png", df=None):
    if df is None:
        df = load_data(excel_path)
    key = category.strip().lower()
    sub = df[df["_cat_key"] == key]
    if sub.empty:
        print(f"Warning: no items found for category '{category}'.")
        return False

    # use the spelling from Excel for display
    display_cat = str(sub.iloc[0]["Category"]).strip()
    st = make_styles()
    keep, cells, missing = [], [], 0

    for _, r in sub.iterrows():
        path = find_image(images_dir, r["Image File"], r["Item Code"])
        img = compressed_image(path, keep) if path else None
        if img is None:
            missing += 1
            img = placeholder(st)
        code = escape(str(r["Item Code"]).strip() or "N/A")
        parts = [img, Spacer(1, 6),
                 Paragraph(escape(trunc(r["Item Name"] or "Unnamed Product", 60)), st["title"]),
                 Paragraph(f"Code: {code}", st["code"]),
                 Spacer(1, 2),
                 Paragraph(escape(format_rate(r["Rate"])), st["price"])]
        desc = str(r["Description"]).strip()
        if desc:
            parts += [Spacer(1, 2), Paragraph(escape(trunc(desc, 95)), st["desc"])]
        cells.append(parts)

    rows = []
    for i in range(0, len(cells), COLS):
        row = cells[i:i + COLS]
        row += [""] * (COLS - len(row))
        rows.append(row)

    col_w = (PAGE_W - 2 * SIDE_MARGIN) / COLS
    table = Table(rows, colWidths=[col_w] * COLS,
                  rowHeights=[ROW_HEIGHT] * len(rows), repeatRows=0)
    table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E0E0E0")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FAFAFA")),
    ]))

    out_dir = os.path.dirname(output_pdf)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    doc = SimpleDocTemplate(output_pdf, pagesize=A4, leftMargin=SIDE_MARGIN,
                            rightMargin=SIDE_MARGIN, topMargin=TOP_MARGIN,
                            bottomMargin=BOTTOM_MARGIN,
                            title=f"{display_cat} Catalog", author=BUSINESS_NAME)
    header = make_header(display_cat, logo_path)
    doc.build([table], onFirstPage=header, onLaterPages=header,
              canvasmaker=NumberedCanvas)
    size_mb = os.path.getsize(output_pdf) / 1048576
    print(f"Created {output_pdf}  ({len(cells)} items, {missing} without image, {size_mb:.1f} MB)")
    return True


def safe_name(s):
    return re.sub(r"[^A-Za-z0-9]+", "_", s.strip()).strip("_") or "Category"


def choose_category(cats):
    print("\nAvailable categories:")
    for i, c in enumerate(cats, 1):
        print(f"  {i}. {c}")
    print("  0. ALL categories")
    while True:
        ans = input("Select a number: ").strip()
        if ans.isdigit() and 0 <= int(ans) <= len(cats):
            return None if ans == "0" else cats[int(ans) - 1]
        print("Invalid choice, try again.")


def main():
    global PHONE
    ap = argparse.ArgumentParser(description="Category-wise PDF catalog generator")
    ap.add_argument("--excel", default="data/website_export.xlsx")
    ap.add_argument("--images", default="product_images")
    ap.add_argument("--out", default="output_catalogs")
    ap.add_argument("--logo", default="assets/logo.png")
    ap.add_argument("--category", help="Category name (case-insensitive)")
    ap.add_argument("--all", action="store_true", help="One PDF per category")
    ap.add_argument("--phone", help="WhatsApp number for the footer")
    a = ap.parse_args()
    if a.phone:
        PHONE = a.phone

    try:
        df = load_data(a.excel)
    except (FileNotFoundError, ValueError) as e:
        sys.exit(f"Error: {e}")
    cats = list_categories(df)
    if not cats:
        sys.exit("No categories found in the Excel file.")

    if a.all:
        targets = cats
    elif a.category:
        targets = [a.category]
    else:
        pick = choose_category(cats)
        targets = cats if pick is None else [pick]

    for cat in targets:
        pdf = os.path.join(a.out, f"{safe_name(cat)}_Catalog.pdf")
        build_catalog(a.excel, a.images, cat, pdf, a.logo, df=df)


if __name__ == "__main__":
    main()
