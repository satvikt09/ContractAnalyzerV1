import fitz
import pytesseract

from PIL import Image


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def extract_text_with_ocr(pdf_path):

    document = fitz.open(pdf_path)

    full_text = ""

    for page_number in range(len(document)):

        page = document.load_page(page_number)

        pix = page.get_pixmap(
            matrix=fitz.Matrix(2, 2)
        )

        mode = "RGB"

        if pix.alpha:
            mode = "RGBA"

        image = Image.frombytes(
            mode,
            [pix.width, pix.height],
            pix.samples
        )

        page_text = pytesseract.image_to_string(
            image,
            lang="eng"
        )

        full_text += page_text + "\n"

    return {
        "text": full_text,
        "page_count": len(document),
        "extraction_method": "ocr"
    }