#!/usr/bin/env python3
from PIL import Image
import os

path = "/icons/logo-lg.png"
file_size = os.path.getsize(path)
img = Image.open(path).convert("RGBA")
pixels = img.load()
w, h = img.size
black = sum(1 for y in range(int(h*0.7), h) for x in range(w) if pixels[x,y][3] > 0 and all(c < 30 for c in pixels[x,y][:3]))
print(f"File size: {file_size}")
print(f"Image size: {img.size}")
print(f"Black pixels bottom 30%: {black}")
