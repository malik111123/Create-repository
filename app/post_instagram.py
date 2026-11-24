"""Post a Reel with the Instagram API (free). Needs a Business or Creator account.

Uses "resumable upload", so the video file is sent directly and does not need a public link.
"""
import time
from pathlib import Path

import requests

from . import config


def _graph(path: str) -> str:
    return f"https://{config.IG_GRAPH_HOST}/{config.IG_API_VERSION}/{path}"


def refresh_token() -> str | None:
    """Long-lived Instagram tokens last 60 days; refreshing gives a new 60 days."""
    if config.IG_GRAPH_HOST != "graph.instagram.com":
        return None
    r = requests.get("https://graph.instagram.com/refresh_access_token",
                     params={"grant_type": "ig_refresh_token", "access_token": config.IG_ACCESS_TOKEN}, timeout=60)
    return r.json().get("access_token") if r.ok else None


def post(video: Path, caption: str) -> str:
    if not (config.IG_USER_ID and config.IG_ACCESS_TOKEN):
        raise RuntimeError("IG_USER_ID / IG_ACCESS_TOKEN missing")
    token = config.IG_ACCESS_TOKEN
    r = requests.post(_graph(f"{config.IG_USER_ID}/media"), data={
        "media_type": "REELS", "upload_type": "resumable", "caption": caption,
        "share_to_feed": "true", "access_token": token}, timeout=60)
    if not r.ok:
        raise RuntimeError(f"Instagram container error: {r.text[:500]}")
    container = r.json()["id"]

    data = video.read_bytes()
    up = requests.post(f"https://rupload.facebook.com/ig-api-upload/{config.IG_API_VERSION}/{container}",
                       headers={"Authorization": f"OAuth {token}", "offset": "0",
                                "file_size": str(len(data))}, data=data, timeout=600)
    if not up.ok:
        raise RuntimeError(f"Instagram upload error: {up.text[:500]}")

    for _ in range(60):  # wait for Instagram to process the video
        s = requests.get(_graph(container), params={"fields": "status_code,status", "access_token": token}, timeout=60).json()
        if s.get("status_code") == "FINISHED":
            break
        if s.get("status_code") == "ERROR":
            raise RuntimeError(f"Instagram processing error: {s}")
        time.sleep(10)
    else:
        raise RuntimeError("Instagram processing timed out")

    pub = requests.post(_graph(f"{config.IG_USER_ID}/media_publish"),
                        data={"creation_id": container, "access_token": token}, timeout=60)
    if not pub.ok:
        raise RuntimeError(f"Instagram publish error: {pub.text[:500]}")
    return pub.json()["id"]
