"""Build a 9:16 ad video from one product photo, using Pillow + ffmpeg. Costs $0."""
import math
import random
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps, features

from . import config

W, H, FPS = 1080, 1920, 30
HOOK_END, POINT_LEN, CTA_LEN = 3.0, 2.2, 3.5
HAS_RAQM = features.check("raqm")
ACCENT = (255, 214, 10)


def _font(size: int, weight: str = "Bold") -> ImageFont.FreeTypeFont:
    path = config.FONTS / f"Vazirmatn-{weight}.ttf"
    layout = ImageFont.Layout.RAQM if HAS_RAQM else ImageFont.Layout.BASIC
    return ImageFont.truetype(str(path), size, layout_engine=layout)


def _is_rtl(text: str) -> bool:
    return any("؀" <= c <= "ۿ" or "ݐ" <= c <= "ݿ" for c in text)


def _shape(text: str) -> str:
    """Without raqm, Arabic-script letters must be joined and reversed by hand."""
    if HAS_RAQM or not _is_rtl(text):
        return text
    import arabic_reshaper
    from bidi.algorithm import get_display
    return get_display(arabic_reshaper.reshape(text))


def _draw_kwargs(text: str) -> dict:
    return {"direction": "rtl" if _is_rtl(text) else "ltr"} if HAS_RAQM else {}


def clean(text: str) -> str:
    """Drop emojis / symbols the bundled font cannot draw (they would show as nothing)."""
    return " ".join("".join(c for c in text if ord(c) < 0x2000 or 0x200c <= ord(c) <= 0x200f).split())


def _wrap(text: str, font, max_w: int) -> list[str]:
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.getlength(_shape(test), **_draw_kwargs(test)) <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_block(text: str, size: int, color=(255, 255, 255), bg=None, max_w: int = 940,
               weight: str = "Black", pad: int = 34) -> Image.Image:
    """Render (possibly multi-line, RTL) text to a transparent image, optional pill background."""
    font = _font(size, weight)
    text = clean(text)
    lines = _wrap(text, font, max_w - 2 * pad)
    line_h = int(size * 1.45)
    widths = [int(font.getlength(_shape(l), **_draw_kwargs(l))) for l in lines]
    bw = max(widths) + 2 * pad
    bh = line_h * len(lines) + pad
    img = Image.new("RGBA", (bw + 20, bh + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if bg:
        shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(shadow).rounded_rectangle((10, 14, bw + 10, bh + 14), radius=bh // 2 if len(lines) == 1 else 40, fill=(0, 0, 0, 110))
        img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(8)))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((10, 10, bw + 10, bh + 10), radius=bh // 2 if len(lines) == 1 else 40, fill=bg)
    for i, (line, lw) in enumerate(zip(lines, widths)):
        x = 10 + (bw - lw) // 2
        y = 10 + pad // 2 + i * line_h + int(size * 0.05)
        kw = _draw_kwargs(line)
        if not bg:
            d.text((x + 3, y + 4), _shape(line), font=font, fill=(0, 0, 0, 160), **kw)
        d.text((x, y), _shape(line), font=font, fill=color, **kw)
    return img


def _ease_out_back(t: float) -> float:
    t = max(0.0, min(1.0, t))
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def _pop(layer: Image.Image, t: float) -> tuple[Image.Image, int]:
    """Scale-in + fade for a text layer. Returns (frame-layer, alpha 0-255)."""
    if t <= 0:
        return layer, 0
    s = max(0.05, _ease_out_back(min(1, t / 0.35)))
    a = int(255 * min(1, t / 0.2))
    if abs(s - 1) > 0.01:
        layer = layer.resize((max(1, int(layer.width * s)), max(1, int(layer.height * s))), Image.BILINEAR)
    return layer, a


def _paste_center(frame: Image.Image, layer: Image.Image, cy: int, alpha: int = 255, cx: int = W // 2):
    if alpha <= 0:
        return
    if alpha < 255:
        layer = layer.copy()
        layer.putalpha(layer.getchannel("A").point(lambda v: v * alpha // 255))
    frame.alpha_composite(layer, (cx - layer.width // 2, cy - layer.height // 2))


def _card(photo: Image.Image) -> Image.Image:
    """Product photo as a rounded card with a soft shadow."""
    max_w, max_h = 820, 960
    card = ImageOps.contain(photo, (max_w, max_h), Image.LANCZOS).convert("RGBA")
    mask = Image.new("L", card.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *card.size), radius=48, fill=255)
    card.putalpha(mask)
    m = 60
    out = Image.new("RGBA", (card.width + 2 * m, card.height + 2 * m), (0, 0, 0, 0))
    sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((m, m + 18, m + card.width, m + card.height + 18), radius=48, fill=(0, 0, 0, 150))
    out = Image.alpha_composite(out, sh.filter(ImageFilter.GaussianBlur(26)))
    out.alpha_composite(card, (m, m))
    return out


def _background(photo: Image.Image) -> Image.Image:
    bg = ImageOps.fit(photo, (W + 120, H + 200), Image.LANCZOS).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg.convert("RGB"), Image.new("RGB", bg.size, (15, 15, 20)), 0.45)
    # gradient: darker top & bottom so text is readable
    grad = Image.new("L", (1, bg.height))
    for y in range(bg.height):
        r = y / bg.height
        grad.putpixel((0, y), int(170 * max(0, 1 - r * 3.2) + 190 * max(0, (r - 0.62) * 2.6)))
    dark = Image.new("RGB", bg.size, (0, 0, 0))
    return Image.composite(dark, bg, grad.resize(bg.size)).convert("RGBA")


def build(photo_path: Path, ad: dict, out_path: Path) -> Path:
    photo = ImageOps.exif_transpose(Image.open(photo_path)).convert("RGB")
    bg = _background(photo)
    card = _card(photo)

    hook = text_block(ad.get("hook", ""), 84)
    points = [text_block(p, 54, color=(20, 20, 20), bg=ACCENT + (255,), weight="Bold")
              for p in ad.get("points", [])]
    cta = text_block(ad.get("cta", ""), 70, color=(20, 20, 20), bg=(255, 255, 255, 255))
    shop_text = " · ".join(x for x in (config.SHOP_NAME, config.SHOP_CONTACT) if x)
    shop = text_block(shop_text, 44, weight="Bold") if shop_text else None

    t_points = HOOK_END
    t_cta = t_points + POINT_LEN * len(points)
    duration = t_cta + CTA_LEN
    n_frames = int(duration * FPS)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    music = sorted(config.MUSIC.glob("*.mp3")) + sorted(config.MUSIC.glob("*.m4a"))
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if music:
        cmd += ["-stream_loop", "-1", "-i", str(random.choice(music)),
                "-af", f"afade=t=in:d=0.5,afade=t=out:st={duration - 1.2:.2f}:d=1.2,volume=0.8",
                "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-b:a", "160k", "-shortest"]
    else:  # silent track: some platforms reject videos with no audio stream
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                "-map", "0:v", "-map", "1:a", "-c:a", "aac", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", "-t", f"{duration:.2f}", str(out_path)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    for i in range(n_frames):
        t = i / FPS
        p = t / duration
        # slow background drift + zoom
        z = 1 + 0.06 * p
        bw, bh = int(bg.width * z), int(bg.height * z)
        b = bg.resize((bw, bh), Image.BILINEAR)
        ox = (bw - W) // 2 + int(30 * math.sin(p * math.pi))
        oy = (bh - H) // 2
        frame = b.crop((ox, oy, ox + W, oy + H))

        # product card: intro slide-up, then slow zoom ("Ken Burns") with gentle float
        intro = _ease_out_back(min(1, t / 0.7))
        cz = (0.85 + 0.15 * intro) * (1 + 0.08 * p)
        c = card.resize((int(card.width * cz), int(card.height * cz)), Image.BILINEAR)
        cy = int(H * 0.52 + (1 - min(1, t / 0.7)) * 500 + 12 * math.sin(t * 2.2))
        _paste_center(frame, c, cy, int(255 * min(1, t / 0.35)))

        if t < t_cta:  # hook stays at top until the CTA
            layer, a = _pop(hook, t - 0.25)
            _paste_center(frame, layer, 250, a)
        for k, pt in enumerate(points):  # benefits pop in one by one and stay
            start = t_points + k * POINT_LEN
            if start <= t < t_cta:
                layer, a = _pop(pt, t - start)
                _paste_center(frame, layer, H - 520 + k * 135, a)
        if t >= t_cta:
            layer, a = _pop(cta, t - t_cta)
            _paste_center(frame, layer, H - 400, a)
            if shop:
                layer, a = _pop(shop, t - t_cta - 0.5)
                _paste_center(frame, layer, H - 260, a)
            _paste_center(frame, hook, 250)

        # fade in / out
        fade = min(1, t / 0.3, (duration - t) / 0.4)
        out = frame.convert("RGB")
        if fade < 1:
            out = Image.blend(Image.new("RGB", out.size), out, max(0, fade))
        proc.stdin.write(out.tobytes())

    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError("ffmpeg failed")
    return out_path
