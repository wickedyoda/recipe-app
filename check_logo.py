#!/usr/bin/env python3
from PIL import Image
img = Image.open("/icons/logo-lg.png").convert("RGBA")
pixels = img.load()
w, h = img.size
black = sum(1 for y in range(int(h*0.7), h) for x in range(w) if pixels[x,y][3] > 0 and all(c < 30 for c in pixels[x,y][:3]))
print(f"Size: {img.size}, Black: {black}")