#!/usr/bin/env python3
"""生成 PWA 图标：靛蓝圆角底 + 白色三横（「三」字的几何形）。只需运行一次。"""
from pathlib import Path

from PIL import Image, ImageDraw

SITE = Path(__file__).resolve().parent.parent / "site"
BG = (45, 85, 216)      # #2D55D8
FG = (255, 255, 255)

img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle([0, 0, 511, 511], radius=116, fill=BG)

# 「三」：上中短、下最长
bars = [  # (width, y_center)
    (236, 164),
    (204, 258),
    (300, 356),
]
H = 46
for w, yc in bars:
    x0 = (512 - w) // 2
    d.rounded_rectangle([x0, yc - H // 2, x0 + w, yc + H // 2], radius=H // 2, fill=FG)

img.save(SITE / "icon-512.png")
img.resize((192, 192), Image.LANCZOS).save(SITE / "icon-192.png")

flat = Image.new("RGB", (512, 512), BG)  # apple-touch-icon 不要透明角
flat.paste(img, (0, 0), img)
flat.resize((180, 180), Image.LANCZOS).save(SITE / "apple-touch-icon.png")
print("icons written")
