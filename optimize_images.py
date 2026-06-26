from PIL import Image
import os
d = "public/assets"
def conv(src, dst, w, q=82):
    im = Image.open(os.path.join(d, src)).convert("RGB")
    if im.width > w:
        im = im.resize((w, round(im.height * w / im.width)))
    im.save(os.path.join(d, dst), "JPEG", quality=q, optimize=True)
    print(dst, os.path.getsize(os.path.join(d, dst)) // 1024, "KB")

conv("hero.png", "hero.jpg", 1920)
for i in (1, 2, 3):
    conv(f"prop{i}.png", f"prop{i}.jpg", 1100)

lg = Image.open(os.path.join(d, "logo.png"))
if lg.width > 512:
    lg = lg.resize((512, round(lg.height * 512 / lg.width)))
lg.save(os.path.join(d, "logo.png"), optimize=True)
print("logo.png", os.path.getsize(os.path.join(d, "logo.png")) // 1024, "KB")
# rimuovi i png pesanti delle foto (ora .jpg)
for f in ("hero.png", "prop1.png", "prop2.png", "prop3.png"):
    p = os.path.join(d, f)
    if os.path.exists(p): os.remove(p)
print("done")
