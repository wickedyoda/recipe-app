#!/usr/bin/env python3
from PIL import Image
import os

SOURCE = "/work/logo_src.png"
ICONS_DIR = "/icons"

img = Image.open(SOURCE).convert("RGBA")
w, h = img.size

crop_y = int(h * 0.76)
cropped = img.crop((0, 0, w, crop_y))

pixels = cropped.load()
black_before = sum(1 for y in range(int(crop_y * 0.7), crop_y) for x in range(w) if pixels[x,y][3] > 0 and all(c < 30 for c in pixels[x,y][:3]))
print(f"Black pixels BEFORE save: {black_before}")

cropped.save(os.path.join(ICONS_DIR, "logo-lg.png"), "PNG")

img2 = Image.open(os.path.join(ICONS_DIR, "logo-lg.png")).convert("RGBA")
pixels2 = img2.load()
w2, h2 = img2.size
black_after = sum(1 for y in range(int(h2 * 0.7), h2) for x in range(w2) if pixels2[x,y][3] > 0 and all(c < 30 for c in pixels2[x,y][:3]))
print(f"Black pixels AFTER save: {black_after}")
print(f"File size: {os.path.getsize(os.path.join(ICONS_DIR, 'logo-lg.png'))}")
