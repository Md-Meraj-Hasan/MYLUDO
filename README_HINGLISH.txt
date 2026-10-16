LUDO PRO OFFLINE — HTML + JavaScript + Capacitor
================================================

Yeh project supplied Python source `python_ludo(2).py` ko dekh kar banaya gaya HTML/JavaScript port hai. GUI responsive SVG/HTML mein recreate ki gayi hai; original Tkinter widgets automatic convert nahi hote.

Included features/ported rules:
- 2, 3, ya 4 local players; player names 1–12 alphabetic characters with single spaces
- Same Green/Blue/Red/Yellow colour order and 15x15 cross board style
- Four tokens per player; enter board only on 6
- Dice: 6 has 35% chance; 1–5 share the remaining chance
- Safe squares; opponent capture returns token to yard
- Capture unlocks home lane for that player
- Exact roll required to finish; token movement follows source path positions
- Three consecutive sixes cancel the turn snapshot
- Roll again after six, capture, or reaching home
- A same-colour double token stack is protected on normal squares
- Offline; no remote APIs or online assets

IMPORTANT HONEST STATUS
-----------------------
This is a first conversion draft, not a verified 1:1 parity build. The source game's full logic and UI are nontrivial; please test all rules on the browser preview before packaging. In particular, game-end/turn edge cases should be compared against the original Python program. This project has not been built into a signed APK in this environment.

PREVIEW ON COMPUTER
-------------------
Open `www/index.html` in a modern browser. Some browsers restrict local JS files, so if it does not start, use a local static server:
  python -m http.server 8000
then open http://localhost:8000/www/

ANDROID APK SETUP (Node.js required)
-----------------------------------
1. Install Node.js LTS and Android Studio/Android SDK.
2. Extract this ZIP and open a terminal in the extracted `ludo_html_capacitor` folder.
3. Run:
   npm install
   npx cap add android
   npx cap sync android
   npx cap open android
4. In Android Studio, build > Build Bundle(s) / APK(s) > Build APK(s).

After changing anything inside www/ run `npx cap sync android` again.

Source of truth: original Python file is not modified by this project.

Developer credit displayed in game: @cd786hassan
