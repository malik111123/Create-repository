"""One run = take the oldest photo from inbox/, make an ad video, post it, move the photo to done/."""
import json
import shutil
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

from . import analyze, config, post_instagram, post_tiktok


def next_photo() -> Path | None:
    photos = [p for p in config.INBOX.iterdir() if p.suffix.lower() in config.IMAGE_EXTS]
    return min(photos, key=lambda p: p.name) if photos else None


def save_secret(name: str, value: str | None):
    """New tokens are written here; the workflow stores them as GitHub Secrets (needs GH_PAT)."""
    if value:
        print(f"::add-mask::{value}")
        config.OUTPUT.mkdir(exist_ok=True)
        with (config.OUTPUT / "secrets_update.txt").open("a") as f:
            f.write(f"{name}={value}\n")


def make_video(photo: Path, ad: dict, out: Path) -> Path:
    if config.VIDEO_MODE == "veo":
        from . import video_veo
        try:
            return video_veo.build(photo, ad, out)
        except Exception as e:  # no credit / quota -> fall back to the free video
            print(f"Veo failed, using free video instead: {e}")
    from . import video_free
    return video_free.build(photo, ad, out)


def run() -> int:
    photo = next_photo()
    if not photo:
        print("inbox/ is empty - nothing to post.")
        return 0
    print(f"Photo: {photo.name}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    ad = analyze.analyze(photo)
    print(json.dumps(ad, ensure_ascii=False, indent=2))
    caption = analyze.full_caption(ad)
    video = make_video(photo, ad, config.OUTPUT / f"{stamp}_{photo.stem}.mp4")
    print(f"Video: {video}")

    results = {}
    if config.DRY_RUN:
        print("DRY_RUN: not posting.")
    else:
        if config.IG_ACCESS_TOKEN:
            try:
                results["instagram"] = post_instagram.post(video, caption)
                save_secret("IG_ACCESS_TOKEN", post_instagram.refresh_token())
            except Exception as e:
                traceback.print_exc()
                results["instagram_error"] = str(e)
        if config.TIKTOK_REFRESH_TOKEN:
            try:
                token, new_refresh = post_tiktok.access_token()
                if new_refresh != config.TIKTOK_REFRESH_TOKEN:
                    save_secret("TIKTOK_REFRESH_TOKEN", new_refresh)
                results["tiktok"] = post_tiktok.post(video, caption, token)
            except Exception as e:
                traceback.print_exc()
                results["tiktok_error"] = str(e)
    print("Results:", results)
    if config.DRY_RUN:
        return 0

    tried = any(k.endswith("_error") for k in results)
    posted = any(not k.endswith("_error") for k in results)
    if tried and not posted:
        print("All platforms failed - photo stays in inbox/ to retry next time.")
        return 1

    config.DONE.mkdir(exist_ok=True)
    dest = config.DONE / f"{stamp}_{photo.name}"
    shutil.move(photo, dest)
    dest.with_suffix(".json").write_text(json.dumps(
        {"ad": ad, "caption": caption, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(run())
