import sys

from docx import Document


def convert_docx_to_text(path):
    doc = Document(path)
    text = []
    for para in doc.paragraphs:
        text.append(para.text)
    return "\n".join(text)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/convert_docx.py <path-to-docx>")
        sys.exit(1)
    path = sys.argv[1]
    print(convert_docx_to_text(path))
