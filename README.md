# ئەپی ڕیکلامی خۆکار (Auto Ads) 🛍️🎬

تۆ تەنها **وێنەی بەرهەم** دادەنێیت. ئەپەکە:

1. بە **Gemini** وێنەکە دەخوێنێتەوە (ناوی بەرهەم، سوودەکانی).
2. **ڤیدیۆی ڕیکلام** دروست دەکات (٩:١٦ بۆ تیکتۆک و ڕیلز) بە نووسینی کوردی.
3. کاپشن و **هاشتاگی باش** دەنووسێت.
4. خۆی لە **ئینستاگرام** و **تیکتۆک** پۆستی دەکات، ڕۆژانە ٣ جار لە کاتی گونجاو.

هەموو شتێک لەسەر **GitHub Actions** کار دەکات: **٠ دۆلار**.

---

## 💰 گرنگ: پارە

| بەش | نرخ |
|---|---|
| Gemini (خوێندنەوەی وێنە + نووسینی ڕیکلام) | بێ پارە (free tier) |
| ڤیدیۆ بە ffmpeg (`VIDEO_MODE=free`) | بێ پارە |
| ڤیدیۆی AI وەک نموونەکەت، بە Veo (`VIDEO_MODE=veo`) | **بە پارەیە**، Veo لە free tier ی Gemini API دا نییە |
| GitHub Actions | بێ پارە |
| API ی ئینستاگرام و تیکتۆک | بێ پارە |

ئەو ڤیدیۆیەی لە ئەپی Gemini دروستت کرد (کچێک بەرهەمەکە دەگرێت) بە **Veo** دروست کراوە. لە ڕێگەی API وە Veo پارەی دەوێت. بۆیە ئەپەکە بە شێوەی بنەڕەت ڤیدیۆی **بێ پارە** دروست دەکات (وێنەکەت + جووڵە + نووسینی کوردی). ئەگەر دواتر پارە یان کرێدیتی Google Cloudت هەبوو (هەژماری نوێ زۆرجار کرێدیتی بێ پارەی تاقیکردنەوە وەردەگرێت)، `VIDEO_MODE` بکە بە `veo`. ئەگەر Veo سەرنەکەوت، ئەپەکە خۆی دەگەڕێتەوە سەر ڤیدیۆی بێ پارە.

---

## 📸 بەکارهێنانی ڕۆژانە

1. ئەپی **GitHub** لە مۆبایلەکەت بکەرەوە (یان github.com).
2. بچۆ ناو فۆڵدەری `inbox/` → **Add file → Upload files** → وێنەکان دابنێ → **Commit**.
3. تەواو! هەر جارێک (کاتژمێر ١:٠٧، ٦:٠٧، ٩:٠٧ ی ئێوارە بە کاتی کوردستان) یەک وێنە دەبێتە ڤیدیۆ و پۆست دەکرێت، و وێنەکە دەچێتە `done/`.

> ڕۆژانە ٣ پۆست. ئەگەر ٦ وێنەت دانا، ٢ ڕۆژی پێدەچێت. کاتەکان لە `.github/workflows/autopost.yml` دا دەگۆڕدرێن.

**تاقیکردنەوە بێ پۆستکردن:** Actions → *Auto post ads* → **Run workflow** → `dry_run` ✅. ڤیدیۆکە لە خوارەوەی پەڕەی ڕەنەکە (Artifacts) دادەبەزێنیت.

---

## ⚙️ ڕێکخستن (یەک جار)

لە ڕیپۆکە: **Settings → Secrets and variables → Actions**

### Secrets
| ناو | چییە |
|---|---|
| `GEMINI_API_KEY` | کلیلی Gemini (aistudio.google.com) |
| `IG_USER_ID` | IDی هەژماری ئینستاگرام |
| `IG_ACCESS_TOKEN` | تۆکنی درێژخایەنی ئینستاگرام |
| `TIKTOK_CLIENT_KEY` / `TIKTOK_CLIENT_SECRET` | لە developers.tiktok.com |
| `TIKTOK_REFRESH_TOKEN` | بە `scripts/tiktok_auth.py` وەریدەگریت |
| `GH_PAT` (ئارەزوومەندانە) | بۆ ئەوەی تۆکنەکان خۆیان نوێ ببنەوە |

### Variables (ئارەزوومەندانە)
| ناو | نموونە |
|---|---|
| `SHOP_NAME` | `L'Dora Care` |
| `SHOP_CONTACT` | `WhatsApp 0750 000 0000` |
| `EXTRA_HASHTAGS` | `#هەولێر #سلێمانی #kurdistan` |
| `AD_LANGUAGE` | بنەڕەت: کوردیی سۆرانی |
| `VIDEO_MODE` | `free` (بنەڕەت) یان `veo` |

### ئینستاگرام
1. هەژمارەکەت بکە بە **Professional** (Business یان Creator).
2. لە developers.facebook.com ئەپێک دروست بکە → بەرهەمی **Instagram** زیاد بکە → *API setup with Instagram login*.
3. هەژمارەکەت زیاد بکە و **token** دروست بکە (مۆڵەتی `instagram_business_content_publish`).
4. تۆکن و IDی هەژمار وەک secret دابنێ. تۆکن ٦٠ ڕۆژ دەمێنێت؛ ئەپەکە دوای هەر پۆستێک نوێی دەکاتەوە (ئەگەر `GH_PAT` هەبێت).

### تیکتۆک
1. لە developers.tiktok.com ئەپێک دروست بکە → **Content Posting API** + **Login Kit** زیاد بکە، **Direct Post** چالاک بکە.
2. Redirect URI دابنێ (بۆ نموونە لینکی GitHub Pages ی خۆت).
3. `python scripts/tiktok_auth.py` لێبدە و `TIKTOK_REFRESH_TOKEN` وەربگرە.
4. ⚠️ تا تیکتۆک ئەپەکەت پەسەند نەکات (audit)، ڤیدیۆکان **تایبەت (private)** پۆست دەکرێن. دوای پەسەندکردن گشتی دەبن. داواکاری audit لە پۆرتاڵەکە بنێرە.

### GH_PAT (بۆ نوێبوونەوەی خۆکاری تۆکن)
github.com → Settings → Developer settings → **Fine-grained token** → تەنها ئەم ڕیپۆیە → مۆڵەتی **Secrets: Read and write**.

---

## 🎵 مۆسیقا
فایلی `mp3` ی بێ مافی چاپ (بۆ نموونە YouTube Audio Library یان Pixabay Music) بخە ناو `assets/music/`. ئەپەکە یەکێکیان بە هەڕەمەکی هەڵدەبژێرێت. بێ مۆسیقا ڤیدیۆکە بێدەنگ دەبێت.

## 📁 پێکهاتە
```
inbox/        وێنەی نوێ لێرە دابنێ
done/         وێنەی پۆستکراو + کاپشن و ئەنجام (json)
app/          کۆدەکە
assets/fonts  فۆنتی Vazirmatn (OFL) بۆ نووسینی کوردی
.github/workflows/autopost.yml   کاتی پۆستکردن
```

## 💻 لەسەر کۆمپیوتەر
```bash
pip install -r requirements.txt   # ffmpeg یش پێویستە
GEMINI_API_KEY=... DRY_RUN=1 python -m app.main
```
