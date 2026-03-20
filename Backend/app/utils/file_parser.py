import fitz
from docx import Document
from io import BytesIO

import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text(filename: str, content: bytes):

    filename = filename.lower()

    # -------- TXT --------
    if filename.endswith(".txt"):

        try:
            return content.decode("utf-8")
        except:
            return content.decode("latin1", errors="ignore")


    # -------- PDF --------
    elif filename.endswith(".pdf"):

        text = ""

        pdf = fitz.open(stream=content, filetype="pdf")

        for page in pdf:
            page_text = page.get_text()
            text += page_text

        # If little text detected → probably scanned PDF
        if len(text.strip()) < 50:

            text = ""

            for page in pdf:

                pix = page.get_pixmap()

                img_bytes = pix.tobytes("png")

                img = Image.open(BytesIO(img_bytes))

                ocr_text = pytesseract.image_to_string(img)

                text += ocr_text

        pdf.close()

        return text


    # -------- DOCX --------
    elif filename.endswith(".docx"):

        doc = Document(BytesIO(content))

        text = "\n".join([p.text for p in doc.paragraphs])

        return text


    # -------- IMAGE OCR --------
    elif filename.endswith((".png", ".jpg", ".jpeg")):

        img = Image.open(BytesIO(content))

        text = pytesseract.image_to_string(img)

        return text


    else:
        raise ValueError("Unsupported file type")