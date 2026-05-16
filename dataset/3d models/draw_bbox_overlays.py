"""Draw bounding boxes from annotation JSON onto the corresponding render
for visual verification."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont

ANNOT_DIR = "/home/claude/exemplar9/annotations"
RENDER_DIR = "/home/claude/exemplar9/renders"
OUT_DIR = "/home/claude/exemplar9/bbox_overlays"
os.makedirs(OUT_DIR, exist_ok=True)

CLASS_COLORS = {
    "veg_contact_branch": (220, 70, 70),
    "broken_crossarm": (240, 140, 30),
    "downed_conductor": (235, 60, 60),
    "ice_buildup": (110, 180, 220),
}

def draw_overlay(json_path):
    with open(json_path) as f:
        annot = json.load(f)
    img_path = os.path.join(RENDER_DIR, annot["image"])
    if not os.path.exists(img_path):
        return None
    img = Image.open(img_path).convert("RGBA")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except Exception:
        font = ImageFont.load_default()
    for a in annot["annotations"]:
        b = a["bounding_box_2d"]["pixels"]
        color = CLASS_COLORS.get(a["class"], (255, 255, 0))
        # Thick box
        for offset in range(3):
            draw.rectangle(
                [(b["x_min"] - offset, b["y_min"] - offset),
                 (b["x_max"] + offset, b["y_max"] + offset)],
                outline=color
            )
        # Label background
        label = a["class"]
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.rectangle(
            [(b["x_min"], b["y_min"] - th - 8), (b["x_min"] + tw + 10, b["y_min"])],
            fill=color + (220,)
        )
        draw.text((b["x_min"] + 5, b["y_min"] - th - 5), label, fill=(255, 255, 255), font=font)
    # Status text in upper-left
    status = f"{annot['scene']} | {annot['angle']} | {annot['lighting']}"
    status += f" | visible: {annot['defect_count_visible']}/{annot['defect_count_in_scene']}"
    if annot.get("defects_off_frame"):
        status += " (some off-frame)"
    if annot.get("is_negative_sample"):
        status += " (negative)"
    draw.rectangle([(0, 0), (1024, 30)], fill=(0, 0, 0, 200))
    draw.text((8, 5), status, fill=(255, 255, 255), font=font)
    out_path = os.path.join(OUT_DIR, annot["image"])
    img.convert("RGB").save(out_path, "PNG")
    return out_path

if __name__ == "__main__":
    files = sorted([f for f in os.listdir(ANNOT_DIR) if f.endswith(".json") and not f.startswith("_")])
    for fname in files:
        out = draw_overlay(os.path.join(ANNOT_DIR, fname))
        if out:
            print(f"  {os.path.basename(out)}")
    print(f"Drew {len(files)} overlays into {OUT_DIR}")
