"""Settings, read from environment variables (GitHub Secrets / Variables)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "inbox"
DONE = ROOT / "done"
OUTPUT = ROOT / "output"
FONTS = ROOT / "assets" / "fonts"
MUSIC = ROOT / "assets" / "music"


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


GEMINI_API_KEY = env("GEMINI_API_KEY")
GEMINI_MODEL = env("GEMINI_MODEL", "gemini-2.5-flash")

# "free"  = build the video from the photo with ffmpeg (costs $0)
# "veo"   = generate an AI video with Veo (Gemini API paid tier / Google Cloud credits)
VIDEO_MODE = env("VIDEO_MODE", "free").lower()
VEO_MODEL = env("VEO_MODEL", "veo-3.0-fast-generate-001")

# Language of the on-video text and the post caption
LANGUAGE = env("AD_LANGUAGE", "Kurdish Sorani (Arabic script)")
SHOP_NAME = env("SHOP_NAME", "")
SHOP_CONTACT = env("SHOP_CONTACT", "")  # e.g. "WhatsApp 0750 000 0000"
EXTRA_HASHTAGS = env("EXTRA_HASHTAGS", "")  # e.g. "#erbil #kurdistan"

IG_USER_ID = env("IG_USER_ID")
IG_ACCESS_TOKEN = env("IG_ACCESS_TOKEN")
IG_GRAPH_HOST = env("IG_GRAPH_HOST", "graph.instagram.com")
IG_API_VERSION = env("IG_API_VERSION", "v21.0")

TIKTOK_CLIENT_KEY = env("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = env("TIKTOK_CLIENT_SECRET")
TIKTOK_REFRESH_TOKEN = env("TIKTOK_REFRESH_TOKEN")
# Until TikTok approves (audits) your app, it only allows private posts (SELF_ONLY).
TIKTOK_PRIVACY = env("TIKTOK_PRIVACY", "auto")

DRY_RUN = env("DRY_RUN", "0") in ("1", "true", "yes")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
