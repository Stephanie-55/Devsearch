import fitz

text = "Hello world! This is a test." * 1000

# Try to create a PDF directly from text
try:
    doc = fitz.open("txt", text.encode("utf-8"))
    pdf_bytes = doc.convert_to_pdf()
    pdf = fitz.open("pdf", pdf_bytes)
    print(f"Success! Pages generated: {pdf.page_count}")
except Exception as e:
    print("Failed:", e)
