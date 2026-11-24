"""Read the product photo with Gemini (free tier) and write the ad script."""
import base64
import json
import mimetypes
from pathlib import Path

import requests

from . import config

PROMPT = """You are a social-media marketing expert for a small online shop in Kurdistan.
Look at this product photo. Read every word on the packaging.
Write a short, punchy vertical-video ad (TikTok / Instagram Reels) for it.

Language for hook, points, cta and caption: {language}.
Shop name: {shop}. Contact: {contact}.

Return ONLY JSON with these keys:
{{
  "product_name": "name as printed on the package",
  "category": "e.g. skincare, perfume, clothing",
  "hook": "very short attention hook, max 6 words",
  "points": ["benefit 1 (max 5 words)", "benefit 2", "benefit 3"],
  "cta": "short call to action, max 6 words (e.g. order now)",
  "caption": "engaging post caption, 2-4 short lines, with emojis, mention how to order",
  "hashtags": ["15 relevant hashtags without spaces: mix of Kurdish, Arabic and English, local (Kurdistan/Erbil/Slemani) + product + trending"],
  "veo_prompt": "English prompt for an AI video model: 8-second vertical UGC-style ad of a friendly model in a bright bathroom holding and using exactly this product, showing the package to the camera, natural light, realistic"
}}"""


def _post(payload: dict) -> dict:
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{config.GEMINI_MODEL}:generateContent")
    r = requests.post(url, headers={"x-goog-api-key": config.GEMINI_API_KEY}, json=payload, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"Gemini error {r.status_code}: {r.text[:500]}")
    return r.json()


def analyze(image_path: Path) -> dict:
    if not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing")
    mime = mimetypes.guess_type(image_path.name)[0] or "image/jpeg"
    data = base64.b64encode(image_path.read_bytes()).decode()
    prompt = PROMPT.format(language=config.LANGUAGE,
                           shop=config.SHOP_NAME or "-",
                           contact=config.SHOP_CONTACT or "-")
    resp = _post({
        "contents": [{"parts": [
            {"inline_data": {"mime_type": mime, "data": data}},
            {"text": prompt},
        ]}],
        "generationConfig": {"response_mime_type": "application/json", "temperature": 0.9},
    })
    text = resp["candidates"][0]["content"]["parts"][0]["text"]
    ad = json.loads(text)
    tags = [t if t.startswith("#") else "#" + t for t in ad.get("hashtags", [])]
    tags += [t for t in config.EXTRA_HASHTAGS.split() if t]
    ad["hashtags"] = list(dict.fromkeys(t.replace(" ", "") for t in tags))[:20]
    ad["points"] = ad.get("points", [])[:3]
    return ad


def full_caption(ad: dict) -> str:
    parts = [ad.get("caption", "").strip()]
    if config.SHOP_CONTACT:
        parts.append("📩 " + config.SHOP_CONTACT)
    parts.append(" ".join(ad.get("hashtags", [])))
    return "\n\n".join(p for p in parts if p)
