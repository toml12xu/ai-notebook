"""
Docling Wrapper Script

Provides convenient functions for document conversion using docling.
Handles installation check, common conversion patterns, and batch processing.
"""

import sys
import json
from pathlib import Path
from typing import Union, Literal, Optional


def ensure_docling_installed():
    """Check if docling is installed, provide installation instructions if not."""
    try:
        import docling
        return True
    except ImportError:
        print("Docling is not installed. Install with: pip install docling")
        return False


def convert_document(
    source: Union[str, Path],
    output_format: Literal["markdown", "json", "html", "dict"] = "markdown",
    enable_ocr: bool = False,
    ocr_languages: Optional[list[str]] = None,
) -> Union[str, dict]:
    """
    Convert a single document to the specified format.
    
    Args:
        source: Path to local file or URL
        output_format: Output format - "markdown", "json", "html", or "dict"
        enable_ocr: Enable OCR for scanned documents
        ocr_languages: List of OCR languages (e.g., ["en", "de"])
    
    Returns:
        Converted document content as string or dict
    
    Example:
        >>> result = convert_document("document.pdf", output_format="markdown")
        >>> print(result)
    """
    if not ensure_docling_installed():
        return None
    
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    
    # Configure pipeline options
    format_options = {}
    if enable_ocr or ocr_languages:
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        if ocr_languages:
            pipeline_options.ocr_options.lang = ocr_languages
        format_options["pdf"] = PdfFormatOption(pipeline_options=pipeline_options)
    
    # Create converter and convert
    converter = DocumentConverter(format_options=format_options) if format_options else DocumentConverter()
    result = converter.convert(str(source))
    
    # Export in requested format
    if output_format == "markdown":
        return result.document.export_to_markdown()
    elif output_format == "json":
        return json.dumps(result.document.export_to_dict(), indent=2, ensure_ascii=False)
    elif output_format == "html":
        return result.document.export_to_html()
    elif output_format == "dict":
        return result.document.export_to_dict()
    else:
        raise ValueError(f"Unknown output format: {output_format}")


def batch_convert(
    sources: list[Union[str, Path]],
    output_format: Literal["markdown", "json", "html", "dict"] = "markdown",
    enable_ocr: bool = False,
) -> list[dict]:
    """
    Convert multiple documents in batch.
    
    Args:
        sources: List of file paths or URLs
        output_format: Output format for all documents
        enable_ocr: Enable OCR for scanned documents
    
    Returns:
        List of dicts with 'source' and 'content' keys
    
    Example:
        >>> results = batch_convert(["doc1.pdf", "doc2.docx"])
        >>> for r in results:
        ...     print(f"{r['source']}: {len(r['content'])} chars")
    """
    if not ensure_docling_installed():
        return []
    
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    
    # Configure pipeline options
    format_options = {}
    if enable_ocr:
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        format_options["pdf"] = PdfFormatOption(pipeline_options=pipeline_options)
    
    converter = DocumentConverter(format_options=format_options) if format_options else DocumentConverter()
    
    results = []
    for source in sources:
        try:
            result = converter.convert(str(source))
            
            if output_format == "markdown":
                content = result.document.export_to_markdown()
            elif output_format == "json":
                content = json.dumps(result.document.export_to_dict(), indent=2, ensure_ascii=False)
            elif output_format == "html":
                content = result.document.export_to_html()
            elif output_format == "dict":
                content = result.document.export_to_dict()
            
            results.append({
                "source": str(source),
                "content": content,
                "success": True
            })
        except Exception as e:
            results.append({
                "source": str(source),
                "error": str(e),
                "success": False
            })
    
    return results


def extract_tables(source: Union[str, Path]) -> list[dict]:
    """
    Extract all tables from a document.
    
    Args:
        source: Path to local file or URL
    
    Returns:
        List of tables as dictionaries (can be loaded into pandas)
    
    Example:
        >>> tables = extract_tables("document.pdf")
        >>> import pandas as pd
        >>> df = pd.DataFrame(tables[0]["data"])
    """
    if not ensure_docling_installed():
        return []
    
    from docling.document_converter import DocumentConverter
    
    converter = DocumentConverter()
    result = converter.convert(str(source))
    
    tables = []
    for i, table in enumerate(result.document.tables):
        try:
            tables.append({
                "index": i,
                "data": table.export_to_dataframe().to_dict(orient="records"),
                "num_rows": table.num_rows,
                "num_cols": table.num_cols
            })
        except Exception as e:
            tables.append({
                "index": i,
                "error": str(e)
            })
    
    return tables


def get_document_structure(source: Union[str, Path]) -> dict:
    """
    Get the structural overview of a document (headings, sections, page count).
    
    Args:
        source: Path to local file or URL
    
    Returns:
        Dictionary with document structure information
    """
    if not ensure_docling_installed():
        return {}
    
    from docling.document_converter import DocumentConverter
    
    converter = DocumentConverter()
    result = converter.convert(str(source))
    doc = result.document
    
    # Extract structure
    structure = {
        "num_pages": len(doc.pages) if hasattr(doc, 'pages') else None,
        "num_tables": len(doc.tables) if hasattr(doc, 'tables') else 0,
        "num_figures": len(doc.figures) if hasattr(doc, 'figures') else 0,
        "headings": [],
        "metadata": doc.export_to_dict().get("metadata", {})
    }
    
    # Extract headings from the document
    try:
        for item in doc.iterate_items():
            if hasattr(item, 'label') and 'heading' in str(item.label).lower():
                structure["headings"].append({
                    "text": item.text if hasattr(item, 'text') else str(item),
                    "level": getattr(item, 'level', None)
                })
    except:
        pass
    
    return structure


# CLI interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Docling document converter wrapper")
    parser.add_argument("source", help="Document path or URL")
    parser.add_argument("-f", "--format", choices=["markdown", "json", "html"], 
                        default="markdown", help="Output format")
    parser.add_argument("--ocr", action="store_true", help="Enable OCR")
    parser.add_argument("-o", "--output", help="Output file path")
    
    args = parser.parse_args()
    
    result = convert_document(
        args.source, 
        output_format=args.format,
        enable_ocr=args.ocr
    )
    
    if result:
        if args.output:
            Path(args.output).write_text(result, encoding="utf-8")
            print(f"Output written to {args.output}")
        else:
            print(result)
