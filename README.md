# Raj & Sons – Catalog Generator

Excel + product photos se category-wise PDF catalog banata hai.

## Pehli baar setup (Windows)
1. Python 3.9+ install karein (python.org) – install karte waqt **"Add Python to PATH"** tick karein.
2. `install.bat` par double-click karein (packages install honge).

## Roz ka use
1. Website se export kiya Excel `data/website_export.xlsx` mein rakhein (purani file replace kar dein).
2. Saari photos `product_images/` mein rakhein. Photo ka naam Excel ke `Image File` column jaisa ho, ya Item Code jaisa (`RS-101.jpg`).
3. `run_gui.bat` double-click karein → category chunein → **Generate Selected** (ya **Generate ALL**).
4. PDF `output_catalogs/` folder mein milegi – seedha WhatsApp par bhej sakte hain.

Command line se:
```
python generate_catalog.py                      # menu se category chunein
python generate_catalog.py --category Crockery
python generate_catalog.py --all
python generate_catalog.py --all --phone "+91-98XXXXXXXX"
```

## Zaroori badlav
- `generate_catalog.py` mein `PHONE = "+91-XXXXXXXXXX"` ki jagah apna asli WhatsApp number likhein
  (ya GUI mein number daalein).
- Logo chahiye to `assets/logo.png` rakh dein (optional).

## Excel columns
`Category, Item Code, Item Name, Rate, Description, Image File`
(`Price`, `SKU`, `Image Name` jaise naam bhi pehchane jaate hain.)

## Dhyan rakhein
- Photo na mile to PDF mein "Image Coming Soon" dikhta hai, script rukti nahi.
- `data/` aur `product_images/` mein abhi **sample (test) data** hai – asli data se replace karein.
- Hindi naam/description PDF mein abhi support nahi (standard font Devanagari nahi dikhata).
