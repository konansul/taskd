import os
import pdfplumber
from docx import Document


def read_pdf(file_path):
    text = ''
    try:
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            print(f"Processing PDF with {total_pages} pages...")

            for page_num, page in enumerate(pdf.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text += page_text.strip() + '\n'
                    else:
                        print(f"Warning: Page {page_num} has no extractable text (might contain only images)")
                except Exception as e:
                    print(f"Warning: Failed to extract text from page {page_num}: {e}")
                    continue

            if not text.strip():
                raise ValueError(
                    "No text could be extracted from the PDF. The PDF might contain only images or be corrupted.")

            print(f"Successfully extracted {len(text)} characters from PDF")
            return text.strip()

    except Exception as e:
        raise ValueError(f"Error reading PDF file: {str(e)}")


def read_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    print(f"read_file called with {file_path}, ext={ext}")

    if ext == '.docx':
        print(f"Opening DOCX: {file_path}")
        doc = Document(file_path)
        print(f"DOCX opened successfully")
        return '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])

    elif ext == '.pdf':
        return read_pdf(file_path)

    else:
        raise ValueError("Unsupported file format: Only .docx and .pdf are supported.")