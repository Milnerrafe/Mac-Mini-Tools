import os
import sys
import tempfile

from PIL import Image, ImageFile
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

# ======================================
# SETTINGS
# ======================================

BAR_COLOR = (0x21, 0x24, 0x29)

TOLERANCE = 8
MIN_BAR_HEIGHT = 5

TARGET_DPI = 300  # Change to 600 for ultra-high quality

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


def save_pdf(images, output_pdf):
    # Calculate initial page size based on first image dimensions at TARGET_DPI
    # ReportLab uses points (72 points = 1 inch)
    first_img_w, first_img_h = images[0].size
    initial_page_w = (first_img_w / TARGET_DPI) * 72
    initial_page_h = (first_img_h / TARGET_DPI) * 72

    c = canvas.Canvas(output_pdf, pagesize=(initial_page_w, initial_page_h))

    for index, img in enumerate(images):
        print(f"Adding page {index + 1} at {TARGET_DPI} DPI...")

        img_width, img_height = img.size

        # Convert pixel size to ReportLab points using TARGET_DPI
        pdf_width = (img_width / TARGET_DPI) * 72
        pdf_height = (img_height / TARGET_DPI) * 72

        c.setPageSize((pdf_width, pdf_height))

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            temp_name = tmp.name

            # Save uncompressed high-resolution PNG slice
            img.save(temp_name, format="PNG", compress_level=0, dpi=(TARGET_DPI, TARGET_DPI))

        # Render 1:1 image pixels on high-DPI PDF page canvas
        c.drawImage(
            ImageReader(temp_name),
            0,
            0,
            width=pdf_width,
            height=pdf_height,
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
    input_files = sys.argv[1:]

    if not input_files:
        print("Error: No input files provided by Dropover.")
        sys.exit(1)

    for input_file in input_files:
        if not os.path.isfile(input_file):
            print(f"Skipping invalid path: {input_file}")
            continue

        print(f"\nProcessing file: {input_file}")

        try:
            img = Image.open(input_file).convert("RGB")
        except Exception as e:
            print(f"Failed to open image {input_file}: {e}")
            continue

        print(f"Image size: {img.size}")

        regions = find_regions(img)

        print(f"Found {len(regions)} sections")

        cropped_images = []

        for i, (top, bottom) in enumerate(regions):
            print(f"Cropping section {i + 1}")

            cropped = img.crop((0, top, img.width, bottom))
            cropped_images.append(cropped)

        base, _ = os.path.splitext(input_file)
        output_pdf = f"{base}_textbookpdf.pdf"

        print(f"Creating PDF at {TARGET_DPI} DPI: {output_pdf}")

        save_pdf(cropped_images, output_pdf)

        print("DONE")
        print(f"Saved as: {output_pdf}")


if __name__ == "__main__":
    main()
