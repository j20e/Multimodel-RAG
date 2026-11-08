import pymupdf as fitz
from pathlib import Path

import pytesseract
from PIL import Image


pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def parse_pdf(file_path):
    """
    Extract text, tables, OCR text, and embedded images from a PDF.
    """

    pdf = None

    try:
        pdf = fitz.open(file_path)

        data = []
        table_count = 0
        ocr_page_count = 0
        image_count = 0

        # Directory for extracted images
        image_dir = Path("extracted_images")
        image_dir.mkdir(exist_ok=True)

        for page_number, page in enumerate(
            pdf,
            start=1
        ):

            # --------------------------------
            # 1. Native text / OCR
            # --------------------------------

            text = page.get_text().strip()

            if text:

                data.append({
                    "location": {
                        "type": "page",
                        "number": page_number
                    },
                    "content": {
                        "type": "text",
                        "text": text,
                        "source": "native"
                    }
                })

            else:

                try:

                    pix = page.get_pixmap(
                        matrix=fitz.Matrix(2, 2)
                    )

                    image = Image.frombytes(
                        "RGB",
                        [pix.width, pix.height],
                        pix.samples
                    )

                    ocr_text = pytesseract.image_to_string(
                        image,
                        lang="eng"
                    ).strip()

                    if ocr_text:

                        ocr_page_count += 1

                        data.append({
                            "location": {
                                "type": "page",
                                "number": page_number
                            },
                            "content": {
                                "type": "text",
                                "text": ocr_text,
                                "source": "ocr"
                            }
                        })

                except Exception:
                    continue

            # --------------------------------
            # 2. Tables
            # --------------------------------

            try:

                tables = page.find_tables()

                for table in tables.tables:

                    table_data = table.extract()

                    if not table_data:
                        continue

                    if not any(
                        any(
                            cell is not None
                            and str(cell).strip()
                            for cell in row
                        )
                        for row in table_data
                    ):
                        continue

                    table_count += 1

                    data.append({
                        "location": {
                            "type": "page",
                            "number": page_number
                        },
                        "content": {
                            "type": "table",
                            "data": table_data
                        }
                    })

            except Exception:
                continue

            # --------------------------------
            # 3. Embedded images
            # --------------------------------

            try:

                images = page.get_images(
                    full=True
                )

                for image_index, image_info in enumerate(
                    images,
                    start=1
                ):

                    xref = image_info[0]

                    extracted_image = pdf.extract_image(
                        xref
                    )

                    image_bytes = extracted_image["image"]
                    image_ext = extracted_image["ext"]

                    image_count += 1

                    image_path = (
                        image_dir
                        / f"{Path(file_path).stem}"
                        f"_page_{page_number}"
                        f"_image_{image_index}"
                        f".{image_ext}"
                    )

                    with open(
                        image_path,
                        "wb"
                    ) as image_file:

                        image_file.write(
                            image_bytes
                        )

                    data.append({
                        "location": {
                            "type": "image",
                            "number": image_count
                        },
                        "content": {
                            "type": "image",
                            "image_path": str(
                                image_path
                            ),
                            "source": "embedded"
                        }
                    })

            except Exception:
                continue

        # --------------------------------
        # 4. Metadata
        # --------------------------------

        metadata = {
            "source": Path(file_path).name,
            "file_type": "pdf",
            "page_count": len(pdf),
            "table_count": table_count,
            "ocr_page_count": ocr_page_count,
            "image_count": image_count
        }

        return {
            "metadata": metadata,
            "data": data
        }

    except Exception as e:

        raise ValueError(
            f"Could not parse PDF: {e}"
        )

    finally:

        if pdf is not None:
            pdf.close()