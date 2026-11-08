from pathlib import Path

from .pdf_parser import parse_pdf
from .pptx_parser import parse_pptx
from .docx_parser import parse_docx


def process_file(file_path):
    """
    Detect the file type and send it to the appropriate parser.
    """

    extension = Path(file_path).suffix.lower()

    if extension == ".pdf":
        return parse_pdf(file_path)

    elif extension == ".pptx":
        return parse_pptx(file_path)

    elif extension == ".docx":
        return parse_docx(file_path)

    else:
        raise ValueError(
            f"Unsupported file type: {extension}"
        )