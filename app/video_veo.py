"""Optional: AI video (like the Gemini-app example) with Veo through the Gemini API.

NOTE: Veo is NOT in the Gemini API free tier. It needs billing turned on
(or Google Cloud free-trial credits). Use VIDEO_MODE=free for $0.
"""
import base64
import mimetypes
import time
from pathlib import Path

import requests

from . import config

BASE = "https://generativelanguage.googleapis.com/v1beta"


def build(photo_path: Path, ad: dict, out_path: Path) -> Path:
    mime = mimetypes.guess_type(photo_path.name)[0] or "image/jpeg"
    body = {
        "instances": [{
            "prompt": ad["veo_prompt"],
            "image": {"bytesBase64Encoded": base64.b64encode(photo_path.read_bytes()).decode(),
                      "mimeType": mime},
        }],
        "parameters": {"aspectRatio": "9:16"},
    }
    key = {"key": config.GEMINI_API_KEY}
    r = requests.post(f"{BASE}/models/{config.VEO_MODEL}:predictLongRunning", params=key, json=body, timeout=120)
    if r.status_code != 200:
        raise RuntimeError(f"Veo error {r.status_code}: {r.text[:500]}")
    op = r.json()
    for _ in range(90):  # up to ~15 minutes
        if op.get("done"):
            break
        time.sleep(10)
        op = requests.get(f"{BASE}/{op['name']}", params=key, timeout=60).json()
    if not op.get("done") or "error" in op:
        raise RuntimeError(f"Veo did not finish: {op.get('error', op)}")
    uri = op["response"]["generateVideoResponse"]["generatedSamples"][0]["video"]["uri"]
    video = requests.get(uri, params=key, timeout=300, allow_redirects=True)
    video.raise_for_status()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(video.content)
    return out_path
