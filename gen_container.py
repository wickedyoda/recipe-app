#!/usr/bin/env python3
from PIL import Image
import os

SOURCE = "/work/logo_src.png"
TMP_DIR = "/tmp/icons_new"

img = Image.open(SOURCE).convert("RGBA")
w, h = img.size
crop_y = int(h * 0.76)
cropped = img.crop((0, 0, w, crop_y))

# Check available resampling filters
print(f"LANCZOS: {hasattr(Image, 'LANCZOS')}")
print(f"Resampling.LANCZOS: {hasattr(Image, 'Resampling') and hasattr(Image.Resampling, 'LANCZOS') if hasattr(Image, 'Resampling') else 'N/A'}")

# Try resize and check pixel at specific locations
small = cropped.resize((512, 512), Image.LANCZOS)
pixels = small.load()

# Check bottom corner
print(f"Bottom-right pixel: {pixels[511, 511]}")
print(f"Bottom-left pixel: {pixels[0, 511]}")
print(f"Bottom center pixel: {pixels[256, 511]}")

# Count black pixels
black = sum(1 for y in range(int(512*0.7), 512) for x in range(512) 
            if pixels[x,y][3] > 0 and all(c < 30 for c in pixels[x,y][:3]))
print(f"Black pixels bottom 30%: {black}")

# Save a test image
small.save(os.path.join(TMP_DIR, "test_resize.png"))
os.makedirs(TMP_DIR, exist_ok=True)
small.save(os.path.join(TMP_DIR, "test_resize.png"))
print(f"Test image saved: {os.path.getsize(os.path.join(TMP_DIR, 'test_resize.png'))} bytes")
