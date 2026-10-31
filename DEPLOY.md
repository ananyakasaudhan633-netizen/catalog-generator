# Catalog Generator – Online deploy (Streamlit Community Cloud, free)

Code GitHub par pehle se hai: `ananyakasaudhan633-netizen/catalog-generator`.

## Step 1 – Naya code GitHub par bhejein
```
git add streamlit_app.py DEPLOY.md requirements.txt
git commit -m "Add Streamlit web app"
git push
```

## Step 2 – Deploy
1. https://share.streamlit.io par GitHub se login karein.
2. **Create app** → repository `catalog-generator`, branch `main`, main file `streamlit_app.py`.
3. **Advanced settings → Secrets** mein ye daalein (apna password/number likhein):
   ```
   APP_PASSWORD = "koi-mazboot-password"
   WHATSAPP = "+91-98XXXXXXXX"
   ```
4. **Deploy** dabayein. 2-3 minute mein link mil jayega (jaise `https://xxxx.streamlit.app`).

## Use kaise karein
Link kholein → password → Excel upload → photos ka ZIP upload → category chunein → PDF download.
Photos ka ZIP: `product_images` folder ko right-click → "Compress to ZIP".

## Dhyan rakhein
- **Password zaroori hai**, kyunki PDF mein wholesale rates hain. Bina `APP_PASSWORD` ke link jiske paas ho wo sab dekh sakta hai.
- Repo mein sirf code hai. Excel aur photos GitHub par nahi jaate (`.gitignore`), upload ke time hi use hote hain aur server par save nahi rehte.
- Free plan par app kuch din use na hone par sleep ho jata hai; link kholne par "Wake up" dabana padta hai.
- Photos ZIP ki limit 200 MB hai. Bahut zyada photos hon to category-wise alag ZIP banayein.
