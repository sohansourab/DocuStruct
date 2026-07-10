"""
make_samples.py
----------------
Creates a few synthetic receipt images (PNG) purely with PIL, so the full
DocuStruct pipeline (OCR -> extraction -> storage) can be demoed offline
without needing real scanned receipts.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent

RECEIPTS = [
    {
        "filename": "receipt_cafe.png",
        "lines": [
            "Blue Bottle Coffee",
            "123 Market St, Palo Alto",
            "Date: 2026-06-14",
            "",
            "Latte        2  4.50",
            "Croissant    1  3.25",
            "Bagel        2  2.75",
            "",
            "Subtotal   $17.25",
            "Tax         $1.55",
            "Total      $18.80",
        ],
    },
    {
        "filename": "receipt_hardware.png",
        "lines": [
            "Ace Hardware Store",
            "88 Industrial Ave",
            "Date: 06/20/2026",
            "",
            "Hammer       1  15.00",
            "Nails Box    3  4.00",
            "Paint Can    2  22.50",
            "",
            "Subtotal   $72.00",
            "Tax         $6.12",
            "Total      $78.12",
        ],
    },
    {
        "filename": "receipt_grocery.png",
        "lines": [
            "Green Valley Grocery",
            "45 Farm Road",
            "Date: Jun 25, 2026",
            "",
            "Milk         1  3.50",
            "Bread        2  2.20",
            "Eggs         1  4.00",
            "Apples       5  0.80",
            "",
            "Subtotal   $17.70",
            "Tax         $1.42",
            "Total      $19.12",
        ],
    },
]


def make_receipt_image(lines, out_path):
    width, height = 500, 60 + 34 * len(lines)
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 20)
    except Exception:
        font = ImageFont.load_default()

    y = 20
    for line in lines:
        draw.text((20, y), line, fill="black", font=font)
        y += 34
    img.save(out_path)


if __name__ == "__main__":
    for r in RECEIPTS:
        filename = str(r["filename"])
        make_receipt_image(r["lines"], OUT_DIR / filename)
        print(f"created {filename}")
