"""
Web version of the Catalog Generator (Streamlit).
Run locally:  streamlit run streamlit_app.py
Deploy:       see DEPLOY.md  (Streamlit Community Cloud, free)
"""
import io
import os
import tempfile
import zipfile

import streamlit as st

import generate_catalog as gc

IMG_OK = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGES_ZIP_MB = 200


def extract_images(zip_bytes, dest):
    """Safely unpack a zip of product photos into dest (flat, images only)."""
    count = 0
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        for info in z.infolist():
            name = os.path.basename(info.filename)   # drops folders -> no path tricks
            ext = os.path.splitext(name)[1].lower()
            if info.is_dir() or not name or name.startswith(".") or ext not in IMG_OK:
                continue
            if info.file_size > 15 * 1024 * 1024:
                continue
            with z.open(info) as src, open(os.path.join(dest, name), "wb") as out:
                out.write(src.read())
            count += 1
    return count


def password_gate():
    """Wholesale rates are private: require APP_PASSWORD (set in Streamlit secrets)."""
    try:
        expected = st.secrets.get("APP_PASSWORD", "")
    except Exception:
        expected = ""
    if not expected:
        st.warning("APP_PASSWORD secret set nahi hai - abhi koi bhi link kholkar rates dekh "
                   "sakta hai. DEPLOY.md dekhein.")
        return
    if st.session_state.get("ok"):
        return
    pwd = st.text_input("Password", type="password")
    if pwd:
        if pwd == expected:
            st.session_state["ok"] = True
            st.rerun()
        else:
            st.error("Galat password.")
    st.stop()


st.set_page_config(page_title="Raj & Sons Catalog Generator", page_icon="📒")
st.title("📒 Raj & Sons – Catalog Generator")
password_gate()

try:
    default_phone = st.secrets.get("WHATSAPP", gc.PHONE)
except Exception:
    default_phone = gc.PHONE

excel_file = st.file_uploader("1. Website export (Excel)", type=["xlsx"])
zip_file = st.file_uploader("2. Product photos (ek ZIP file mein)", type=["zip"])
logo_file = st.file_uploader("3. Logo (optional)", type=["png", "jpg", "jpeg"])
phone = st.text_input("WhatsApp number (footer mein dikhega)", value=default_phone)

if excel_file:
    work = tempfile.mkdtemp(prefix="catalog_")
    excel_path = os.path.join(work, "data.xlsx")
    with open(excel_path, "wb") as f:
        f.write(excel_file.getvalue())
    try:
        df = gc.load_data(excel_path)
        cats = gc.list_categories(df)
    except Exception as e:
        st.error(f"Excel padh nahi paye: {e}")
        st.stop()

    choice = st.selectbox("Category", ["ALL categories"] + cats)

    if st.button("Catalog banayein", type="primary"):
        images_dir = os.path.join(work, "images")
        os.makedirs(images_dir, exist_ok=True)
        if zip_file:
            if zip_file.size > MAX_IMAGES_ZIP_MB * 1024 * 1024:
                st.error(f"ZIP {MAX_IMAGES_ZIP_MB} MB se chhoti honi chahiye.")
                st.stop()
            try:
                n = extract_images(zip_file.getvalue(), images_dir)
                st.info(f"{n} photos mili.")
            except zipfile.BadZipFile:
                st.error("Ye valid ZIP file nahi hai.")
                st.stop()
        else:
            st.warning("Photos upload nahi hui - sabme 'Image Coming Soon' dikhega.")

        logo_path = ""
        if logo_file:
            logo_path = os.path.join(work, "logo.png")
            with open(logo_path, "wb") as f:
                f.write(logo_file.getvalue())

        gc.PHONE = phone.strip() or gc.PHONE
        targets = cats if choice == "ALL categories" else [choice]
        pdfs = []
        with st.spinner("PDF ban rahi hai..."):
            for cat in targets:
                out = os.path.join(work, f"{gc.safe_name(cat)}_Catalog.pdf")
                if gc.build_catalog(excel_path, images_dir, cat, out, logo_path, df=df):
                    pdfs.append(out)

        if not pdfs:
            st.error("Koi item nahi mila.")
        elif len(pdfs) == 1:
            with open(pdfs[0], "rb") as f:
                st.download_button("⬇️ PDF download karein", f.read(),
                                   file_name=os.path.basename(pdfs[0]),
                                   mime="application/pdf")
            st.success("Ho gaya!")
        else:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
                for p in pdfs:
                    z.write(p, os.path.basename(p))
            st.download_button("⬇️ Saari PDFs (ZIP)", buf.getvalue(),
                               file_name="All_Catalogs.zip", mime="application/zip")
            st.success(f"{len(pdfs)} catalogs ban gaye!")
else:
    st.caption("Pehle Excel upload karein.")
