import os
import tempfile

from PIL import Image, ImageFile
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# ======================================
# SETTINGS
# ======================================

INPUT_PNG = "input.png"
OUTPUT_PDF = "output.pdf"

BAR_COLOR = (0x21, 0x24, 0x29)

TOLERANCE = 8
MIN_BAR_HEIGHT = 5

PDF_DPI = 300  # High quality

# ======================================
# ALLOW HUGE IMAGES
# ======================================

Image.MAX_IMAGE_PIXELS = None
ImageFile.LOAD_TRUNCATED_IMAGES = True

# ======================================
# BAR DETECTION
# ======================================


def is_bar_row(row_pixels):
    for pixel in row_pixels:
        r, g, b = pixel[:3]

        if (
            abs(r - BAR_COLOR[0]) > TOLERANCE
            or abs(g - BAR_COLOR[1]) > TOLERANCE
            or abs(b - BAR_COLOR[2]) > TOLERANCE
        ):
            return False

    return True


def find_regions(img):
    width, height = img.size
    pixels = img.load()

    bars = []

    in_bar = False
    start_y = 0

    print("Scanning for separator bars...")

    for y in range(height):
        row = [pixels[x, y] for x in range(width)]

        if is_bar_row(row):
            if not in_bar:
                in_bar = True
                start_y = y

        else:
            if in_bar:
                in_bar = False
                end_y = y - 1

                if (end_y - start_y + 1) >= MIN_BAR_HEIGHT:
                    bars.append((start_y, end_y))

    if in_bar:
        end_y = height - 1

        if (end_y - start_y + 1) >= MIN_BAR_HEIGHT:
            bars.append((start_y, end_y))

    regions = []

    current_top = 0

    for start, end in bars:
        if start > current_top:
            regions.append((current_top, start))

        current_top = end + 1

    if current_top < height:
        regions.append((current_top, height))

    return regions


# ======================================
# PDF CREATION
# ======================================


def save_pdf(images):

    page_width, page_height = A4

    c = canvas.Canvas(OUTPUT_PDF, pagesize=A4)

    for index, img in enumerate(images):
        print(f"Adding page {index + 1}")

        img_width, img_height = img.size

        scale = min(page_width / img_width, page_height / img_height)

        draw_width = img_width * scale
        draw_height = img_height * scale

        x = (page_width - draw_width) / 2
        y = (page_height - draw_height) / 2

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            temp_name = tmp.name

            # Save lossless PNG
            img.save(temp_name, format="PNG", compress_level=0)

        c.drawImage(
            ImageReader(temp_name),
            x,
            y,
            width=draw_width,
            height=draw_height,
            preserveAspectRatio=True,
            mask="auto",
        )

        os.remove(temp_name)

        c.showPage()

    c.save()


# ======================================
# MAIN
# ======================================


def main():

    print("Opening image...")

    img = Image.open(INPUT_PNG).convert("RGB")

    print(f"Image size: {img.size}")

    regions = find_regions(img)

    print(f"Found {len(regions)} sections")

    cropped_images = []

    for i, (top, bottom) in enumerate(regions):
        print(f"Cropping section {i + 1}")

        cropped = img.crop((0, top, img.width, bottom))

        cropped_images.append(cropped)

    print("Creating high-quality PDF...")

    save_pdf(cropped_images)

    print("DONE")
    print(f"Saved as: {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
