# GitHub Actions par Bot Chalana (100% Free, koi server nahi chahiye)

Ye tarika bilkul free hai — koi VPS, koi credit card, koi expiry nahi. GitHub khud
har thodi der me aapka bot chala dega, market hours me.

---

## Step 1 — GitHub Account Banana

1. **github.com** par jaayein → "Sign up" → sirf email, username, password se account ban jata hai (koi card nahi chahiye)

## Step 2 — Naya Repository Banana

1. Login karke top-right "+" → **"New repository"**
2. Naam dein (jaise `my-paper-trading-bot`)
3. **Private** rakhein (zaroori — takaki koi aur aapka code na dekh sake)
4. "Create repository" dabayein

## Step 3 — Files Upload Karna

1. Repository page par **"uploading an existing file"** link par click karein
2. Is folder ki saari files (jo maine di hain) drag-drop kar dein — `config.py`, `run_once.py`, `report.py`, `indicators.py`, `angel_api.py`, `scrip_master.py`, `strategy.py`, `portfolio.py`, `notifier.py`, `requirements.txt`, aur `.github/workflows/scan.yml` (ye workflow folder automatically sahi jagah chala jayega agar aap poora folder structure drag karein — GitHub Desktop app se karna sabse aasan rahega, neeche bataya hai)

**Aasan tarika**: **GitHub Desktop** app (desktop.github.com se free download) install kar lein — usse pura folder ek click me upload (push) ho jata hai, structure bhi sahi rehta hai.

## Step 4 — Secrets Add Karna (API keys chhupane ke liye)

1. Repository ke andar **Settings** tab
2. Left side **Secrets and variables → Actions**
3. **"New repository secret"** — ek-ek karke ye sab add karein:

| Secret Name | Value |
|---|---|
| `ANGEL_API_KEY` | Aapki Angel One API Key |
| `ANGEL_CLIENT_CODE` | Aapka Angel One Client ID |
| `ANGEL_PASSWORD` | Aapka Angel One MPIN |
| `ANGEL_TOTP_SECRET` | TOTP secret key |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Telegram chat ID |

## Step 5 — Workflow Chalu Karna

1. Repository me **"Actions"** tab par jaayein
2. "Paper Trading Bot Scan" workflow dikhega — usme **"Enable workflow"** dabayein (agar disable dikhe)
3. Test karne ke liye: right side **"Run workflow"** button se ek baar manually chala kar dekh lein
4. "Actions" tab me hi uska output/logs dikh jayenge — check karein "Angel One login safal" aa raha hai ya nahi

Bas ho gaya! Ab ye har market din, har 10 minute me (9:15 AM – 3:30 PM IST) automatically chalega —
koi laptop/mobile ON rakhne ki zaroorat nahi.

---

## Report Nikalna

Apne PC par is repo ko clone/download karke (ya GitHub Desktop se "pull" karke):

```bash
python report.py
```

CSV ban jayegi. (`data/state.json` file me hamesha latest portfolio data GitHub par hi save rehta hai — bot khud usse commit kar deta hai.)

---

## Zaroori Baatein

- **Repository "Private" hi rakhein** — warna kisi bhi security ke bawajood aapka code (business logic) sab dekh sakte hain (secrets phir bhi safe rahengi, par private zyada surakshit hai)
- GitHub free plan me **private repo ke Actions minutes** bhi free quota me aate hain (is chhote bot ke liye woh kaafi hai, khatam hone ka chance kam hai)
- **Important**: Agar 60 din tak repository me koi activity na ho, GitHual automatically scheduled workflows ko pause kar deta hai — bas kabhi-kabhi "Actions" tab check kar liya karein ki chalu hai
- Bot sirf paper trading karta hai, koi real order nahi — same jaisa pehle bataya tha
