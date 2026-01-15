import os
import sys
import argparse
from ebooklib import epub
from fpdf import FPDF
from bs4 import BeautifulSoup
import warnings
from ebooklib import epub

# Suppress specific warnings
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'EPUB to PDF Conversion', 0, 1, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body.encode('latin-1', 'replace').decode('latin-1'))
        self.ln()

def epub_to_pdf(epub_file, pdf_file):
    try:
        book = epub.read_epub(epub_file)
        pdf = PDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        for item in book.get_items():
            if item.media_type == 'application/xhtml+xml':
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text = soup.get_text()
                pdf.chapter_body(text)

        pdf.output(pdf_file)
        print(f"Successfully converted {epub_file} to {pdf_file}")

    except FileNotFoundError:
        print(f"Error: The file {epub_file} was not found.")
    except PermissionError:
        print(f"Error: Permission denied when accessing {epub_file} or {pdf_file}.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Convert EPUB files to PDF.")
    parser.add_argument("-f", "--file", required=True, help="Path to the EPUB file")

    args = parser.parse_args()
    epub_file = args.file

    if not epub_file.lower().endswith('.epub'):
        print("Error: The file must have a .epub extension.")
        sys.exit(1)

    pdf_file = os.path.splitext(epub_file)[0] + ".pdf"
    epub_to_pdf(epub_file, pdf_file)

if __name__ == "__main__":
    main()

