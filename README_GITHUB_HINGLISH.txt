LUDO ANDROID APK — GITHUB ACTIONS (JAVA 21)
==========================================

GitHub par upload karne ke liye:
1. ZIP extract kijiye.
2. GitHub repository open kijiye.
3. Add file > Upload files par click kijiye.
4. Extracted folder ke ANDAR ka sab content repository ke root mein upload kijiye.
   .github folder bhi upload hona chahiye. Uske andar workflows/build-apk.yml hai.
5. Commit changes kijiye.
6. Repository ke Actions tab mein "Build Ludo Android APK" workflow kholiye.
7. Build complete hone par Ludo-Android-APK artifact download kijiye; us ZIP ke andar app-debug.apk hoga.

ZAROORI:
- Build workflow Node 22 aur Java 21 use karta hai.
- Android app `www/index.html`, `www/app.js`, aur `www/style.css` wale HTML/JavaScript game se banta hai.
- `reference/Ludo_Original_Design_GUI_Match_v20.py` reference ke liye rakhi hai; Android APK directly Tkinter/Python file ko run nahi karta.
- APK workflow se build hota hai, lekin yahan GitHub Actions run karke APK verify nahi kiya gaya.
- `node_modules` upload karne ki zaroorat nahi.
