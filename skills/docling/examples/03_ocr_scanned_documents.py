"""
OCR for Scanned Documents

This example shows how to process scanned PDFs and images using OCR.
"""

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions


def convert_scanned_pdf(pdf_path: str, languages: list = None):
    """
    Convert a scanned PDF using OCR.
    
    Args:
        pdf_path: Path to scanned PDF file
        languages: List of OCR languages (e.g., ["en", "de", "fr"])
        
    Returns:
        Markdown content extracted via OCR
    """
    # Configure OCR pipeline
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    
    if languages:
        pipeline_options.ocr_options.lang = languages
    
    converter = DocumentConverter(
        format_options={
            "pdf": PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    
    result = converter.convert(pdf_path)
    return result.document.export_to_markdown()


def convert_image(image_path: str, languages: list = None):
    """
    Extract text from an image using OCR.
    
    Args:
        image_path: Path to image file (PNG, JPEG, TIFF, etc.)
        languages: List of OCR languages
        
    Returns:
        Extracted text as Markdown
    """
    from docling.document_converter import ImageFormatOption
    from docling.datamodel.pipeline_options import ImagePipelineOptions
    
    pipeline_options = ImagePipelineOptions()
    pipeline_options.do_ocr = True
    
    if languages:
        pipeline_options.ocr_options.lang = languages
    
    converter = DocumentConverter(
        format_options={
            "image": ImageFormatOption(pipeline_options=pipeline_options)
        }
    )
    
    result = converter.convert(image_path)
    return result.document.export_to_markdown()


def batch_ocr(file_paths: list, languages: list = None):
    """
    Process multiple scanned documents with OCR.
    
    Args:
        file_paths: List of file paths
        languages: OCR languages
        
    Returns:
        List of results with source and content
    """
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    
    if languages:
        pipeline_options.ocr_options.lang = languages
    
    converter = DocumentConverter(
        format_options={
            "pdf": PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    
    results = []
    for path in file_paths:
        try:
            result = converter.convert(path)
            results.append({
                "source": path,
                "content": result.document.export_to_markdown(),
                "success": True
            })
        except Exception as e:
            results.append({
                "source": path,
                "error": str(e),
                "success": False
            })
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        path = sys.argv[1]
        print(f"Processing with OCR: {path}")
        
        # Default to English, German, French
        content = convert_scanned_pdf(path, languages=["en"])
        print(content[:1000])
    else:
        print("Usage: python 03_ocr_scanned_documents.py <scanned_pdf_path>")
        print("\nSupported OCR languages: en, de, fr, es, it, pt, zh, ja, ko, etc.")
