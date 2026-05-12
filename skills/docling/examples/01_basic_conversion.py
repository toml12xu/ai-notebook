"""
Basic Document Conversion with Docling

This example shows how to convert documents to different formats.
"""

from docling.document_converter import DocumentConverter


def basic_pdf_to_markdown():
    """Convert a PDF to Markdown."""
    converter = DocumentConverter()
    
    # Convert from URL
    result = converter.convert("https://arxiv.org/pdf/2408.09869")
    
    # Export to Markdown
    markdown = result.document.export_to_markdown()
    print(markdown[:500])  # Print first 500 chars
    
    return markdown


def convert_local_file(file_path: str):
    """Convert a local document file."""
    converter = DocumentConverter()
    result = converter.convert(file_path)
    
    # Export options
    markdown = result.document.export_to_markdown()
    json_dict = result.document.export_to_dict()
    html = result.document.export_to_html()
    
    return {
        "markdown": markdown,
        "json": json_dict,
        "html": html
    }


def convert_multiple_files(file_paths: list):
    """Convert multiple files efficiently."""
    converter = DocumentConverter()
    
    results = []
    for path in file_paths:
        result = converter.convert(path)
        results.append({
            "source": path,
            "markdown": result.document.export_to_markdown()
        })
    
    return results


if __name__ == "__main__":
    # Example: Convert the Docling technical report
    print("Converting Docling Technical Report...")
    md = basic_pdf_to_markdown()
    print(f"\nConverted {len(md)} characters to Markdown")
