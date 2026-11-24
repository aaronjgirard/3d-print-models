## Copyright 2026 Aaron Girard
## SPDX-License-Identifier: Apache-2.0
"""Six-panel overview sheet from the renders (out/track_overview.png)."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageChops

R = "out/renders"
PANELS = [("straight.png", "Straight, 164 mm"), ("curve.png", "Curve, 22.5 deg, R 412 mm"),
          ("grain_ties.png", "Wood grain on the tie tops"), ("prong_L.png", "Prong end: raised L, thin plate from the rail end"),
          ("joint_orig_male.png", "Original tab end (blue) in a printed prong end"),
          ("joint_orig_female.png", "Printed tab end in an original prong end (blue)")]


def main(out="out/track_overview.png", W=800, H=500):
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
    sheet = Image.new("RGB", (2 * W, 3 * H), "white")
    for i, (f, label) in enumerate(PANELS):
        im = Image.open(os.path.join(R, f)).convert("RGB")
        bbox = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
        if bbox:
            im = im.crop((max(0, bbox[0] - 30), max(0, bbox[1] - 30), min(im.width, bbox[2] + 30), min(im.height, bbox[3] + 30)))
        im.thumbnail((W - 20, H - 60))
        x0, y0 = (i % 2) * W, (i // 2) * H
        sheet.paste(im, (x0 + (W - im.width) // 2, y0 + 50 + (H - 60 - im.height) // 2))
        ImageDraw.Draw(sheet).text((x0 + 20, y0 + 12), label, fill=(20, 20, 20), font=font)
    sheet.save(out)
    return out


if __name__ == "__main__":
    print(main())
