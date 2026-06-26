from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageGrab


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
DOC_ASSETS = ROOT / "docs" / "assets"


def ensure_dirs() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    DOC_ASSETS.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        "segoeuib.ttf" if bold else "segoeui.ttf",
        "arialbd.ttf" if bold else "arial.ttf",
    )
    for name in candidates:
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            pass
    return ImageFont.load_default()


def make_icon() -> None:
    base = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)
    draw.rounded_rectangle((38, 38, 474, 474), radius=112, fill="#0f766e")
    draw.rounded_rectangle((72, 72, 440, 440), radius=90, outline="#99f6e4", width=10)

    draw.rounded_rectangle((196, 126, 316, 310), radius=58, fill="#f8fafc")
    draw.rounded_rectangle((222, 148, 290, 290), radius=34, fill="#0f766e")
    draw.line((154, 242, 154, 278), fill="#f8fafc", width=22)
    draw.arc((154, 188, 358, 348), start=0, end=180, fill="#f8fafc", width=22)
    draw.line((256, 344, 256, 390), fill="#f8fafc", width=22)
    draw.rounded_rectangle((196, 386, 316, 410), radius=12, fill="#f8fafc")

    shine = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
    shine_draw = ImageDraw.Draw(shine)
    shine_draw.polygon(((86, 64), (278, 64), (64, 278)), fill=(255, 255, 255, 30))
    base.alpha_composite(shine)

    base.save(ASSETS / "itoldu.png")
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    base.save(ASSETS / "itoldu.ico", sizes=sizes)


def draw_mock_screenshot(path: Path) -> None:
    img = Image.new("RGB", (1280, 900), "#f6f8f7")
    draw = ImageDraw.Draw(img)

    draw.rectangle((0, 0, 1280, 68), fill="#0f172a")
    draw.text((34, 18), "I Told U", fill="#f8fafc", font=font(26, True))
    draw.rounded_rectangle((1088, 18, 1245, 50), radius=16, fill="#0f766e")
    draw.text((1114, 24), "Hotkey: -", fill="#ffffff", font=font(15, True))

    draw.text((42, 105), "Voice typing, translation, paste anywhere.", fill="#0f172a", font=font(30, True))
    draw.text((44, 148), "Hold a key, speak, release. The result lands in your active window.", fill="#475569", font=font(18))

    card = (38, 205, 836, 690)
    draw.rounded_rectangle(card, radius=18, fill="#ffffff", outline="#d8ded9", width=2)
    draw.text((70, 236), "Controls", fill="#0f172a", font=font(18, True))

    items = [
        ("App enabled", True),
        ("DeepSeek translation", False),
        ("Paste to active window", True),
    ]
    y = 285
    for label, active in items:
        draw.rounded_rectangle((72, y, 100, y + 28), radius=7, fill="#0f766e" if active else "#ffffff", outline="#9ca3af")
        if active:
            draw.line((79, y + 15, 87, y + 22, 95, y + 8), fill="#ffffff", width=3)
        draw.text((116, y + 3), label, fill="#0f172a", font=font(16))
        y += 46

    fields = [
        ("Push-to-talk hotkey", "-"),
        ("Speech driver", "google"),
        ("Speech language", "Auto PL/EN"),
        ("Target language", "polski"),
        ("App language", "English"),
    ]
    y = 432
    for label, value in fields:
        draw.text((72, y + 8), label, fill="#475569", font=font(14))
        draw.rounded_rectangle((282, y, 790, y + 36), radius=8, fill="#f8fafc", outline="#cfd8d2")
        draw.text((302, y + 8), value, fill="#0f172a", font=font(15))
        y += 48

    side = (870, 205, 1242, 690)
    draw.rounded_rectangle(side, radius=18, fill="#ffffff", outline="#d8ded9", width=2)
    draw.text((902, 236), "Small overlay", fill="#0f172a", font=font(18, True))
    draw.text((902, 273), "Minimal status badges stay in the corner.", fill="#64748b", font=font(15))
    overlay = (956, 338, 1160, 404)
    draw.rounded_rectangle(overlay, radius=22, fill="#0b1220", outline="#134e4a", width=2)
    for i, color in enumerate(("#ef4444", "#22c55e", "#38bdf8")):
        x = 982 + i * 58
        draw.ellipse((x, 354, x + 28, 382), fill=color)

    draw.rounded_rectangle((38, 725, 1242, 858), radius=18, fill="#ffffff", outline="#d8ded9", width=2)
    draw.text((70, 754), "Preview", fill="#0f172a", font=font(18, True))
    draw.text((70, 800), "Ostatni wynik pojawi sie tutaj.", fill="#475569", font=font(17))

    img.save(path)


def capture_app_screenshot(path: Path) -> bool:
    try:
        import pygetwindow as gw
    except Exception:
        return False

    env = os.environ.copy()
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    proc = subprocess.Popen(
        [sys.executable, str(ROOT / "app.py")],
        cwd=str(ROOT),
        env=env,
        creationflags=creationflags,
    )
    try:
        window = None
        for _ in range(60):
            matches = [win for win in gw.getWindowsWithTitle("I Told U") if win.width > 300 and win.height > 200]
            if matches:
                window = matches[0]
                break
            time.sleep(0.2)
        if window is None:
            return False

        try:
            window.restore()
            window.activate()
        except Exception:
            pass
        time.sleep(0.8)

        left = max(0, int(window.left))
        top = max(0, int(window.top))
        right = max(left + 1, int(window.left + window.width))
        bottom = max(top + 1, int(window.top + window.height))
        shot = ImageGrab.grab(bbox=(left, top, right, bottom))
        shot.save(path)
        return True
    except Exception:
        return False
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=4)
        except subprocess.TimeoutExpired:
            proc.kill()


def main() -> None:
    ensure_dirs()
    make_icon()
    screenshot = DOC_ASSETS / "screenshot.png"
    draw_mock_screenshot(screenshot)
    print(f"Wrote {ASSETS / 'itoldu.ico'}")
    print(f"Wrote {screenshot}")


if __name__ == "__main__":
    main()
