#!/usr/bin/env python3
from PIL import Image
import os

SOURCE = "/work/logo_src.png"
ICONS_DIR = "/icons"

img = Image.open(SOURCE).convert("RGBA")
w, h = img.size

crop_y = int(h * 0.76)
cropped = img.crop((0, 0, w, crop_y))

# Verify
pixels = cropped.load()
black = sum(1 for y in range(int(crop_y * 0.7), crop_y) for x in range(w) if pixels[x,y][3] > 0 and all(c < 30 for c in pixels[x,y][:3]))
print(f"Black pixels: {black}")

sizes = {
    "favicon-16x16.png": 16,
    "favicon-32x32.png": 32,
    "favicon-48x48.png": 48,
    "favicon-96x96.png": 96,
    "favicon-128x128.png": 128,
    "favicon-180x180.png": 180,
    "favicon-192x192.png": 192,
    "favicon-256x256.png": 256,
    "favicon-384x384.png": 384,
    "favicon-512x512.png": 512,
    "apple-touch-icon.png": 180,
    "android-chrome-192x192.png": 192,
    "android-chrome-512x512.png": 512,
    "android-chrome-192x192-maskable.png": 192,
    "android-chrome-512x512-maskable.png": 512,
    "logo-lg.png": 512,
    "logo-sm.png": 64,
}

for filename, size in sizes.items():
    resized = cropped.resize((size, size), Image.LANCZOS)
    resized.save(os.path.join(ICONS_DIR, filename), "PNG")
    print(f"  OK {filename} ({size}x{size})")

cropped.save(os.path.join(ICONS_DIR, "favicon.ico"), "ICO", sizes=[(16,16),(32,32),(48,48)])
print("  OK favicon.ico")
print("Done!")
