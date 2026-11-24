"""Post a video with the TikTok Content Posting API (free).

Until TikTok audits (approves) your app, posts can only be private (SELF_ONLY).
After approval they can be public.
"""
from pathlib import Path

import requests

from . import config

API = "https://open.tiktokapis.com/v2"


def access_token() -> tuple[str, str]:
    """TikTok access tokens last 24h, so get a fresh one from the refresh token (valid 365 days)."""
    r = requests.post(f"{API}/oauth/token/", data={
        "client_key": config.TIKTOK_CLIENT_KEY, "client_secret": config.TIKTOK_CLIENT_SECRET,
        "grant_type": "refresh_token", "refresh_token": config.TIKTOK_REFRESH_TOKEN}, timeout=60)
    j = r.json()
    if "access_token" not in j:
        raise RuntimeError(f"TikTok token error: {j}")
    return j["access_token"], j.get("refresh_token", config.TIKTOK_REFRESH_TOKEN)


def _privacy(headers: dict) -> str:
    if config.TIKTOK_PRIVACY != "auto":
        return config.TIKTOK_PRIVACY
    r = requests.post(f"{API}/post/publish/creator_info/query/", headers=headers, timeout=60).json()
    options = r.get("data", {}).get("privacy_level_options", [])
    return "PUBLIC_TO_EVERYONE" if "PUBLIC_TO_EVERYONE" in options else "SELF_ONLY"


def post(video: Path, caption: str, token: str) -> str:
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"}
    size = video.stat().st_size
    chunk = size if size <= 64 * 1024 * 1024 else 10 * 1024 * 1024
    count = max(1, size // chunk)  # TikTok: last chunk absorbs the remainder
    init = requests.post(f"{API}/post/publish/video/init/", headers=headers, json={
        "post_info": {"title": caption[:2200], "privacy_level": _privacy(headers),
                      "disable_comment": False, "disable_duet": False, "disable_stitch": False},
        "source_info": {"source": "FILE_UPLOAD", "video_size": size,
                        "chunk_size": chunk, "total_chunk_count": count},
    }, timeout=60).json()
    if init.get("error", {}).get("code") not in (None, "ok"):
        raise RuntimeError(f"TikTok init error: {init['error']}")
    upload_url = init["data"]["upload_url"]

    with video.open("rb") as f:
        for i in range(count):
            start = i * chunk
            end = size - 1 if i == count - 1 else start + chunk - 1
            f.seek(start)
            part = f.read(end - start + 1)
            r = requests.put(upload_url, data=part, timeout=600, headers={
                "Content-Type": "video/mp4", "Content-Length": str(len(part)),
                "Content-Range": f"bytes {start}-{end}/{size}"})
            if r.status_code not in (200, 201, 206):
                raise RuntimeError(f"TikTok upload error {r.status_code}: {r.text[:300]}")
    return init["data"]["publish_id"]
