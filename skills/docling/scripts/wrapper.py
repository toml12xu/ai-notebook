"""
Docling Wrapper Script

Provides convenient functions for document conversion using docling.
Handles installation check, common conversion patterns, and batch processing.
"""

import os
import sys
import io
import json
import glob
import zipfile
import xml.etree.ElementTree as ET
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


def _fix_stdout_encoding():
    """Fix stdout encoding for Windows with non-ASCII filenames."""
    if sys.platform == "win32" and hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def _convert_corrupted_docx(docx_path: str) -> Optional[str]:
    """
    Fallback: extract text from a corrupted DOCX by parsing document.xml directly.
    Handles files with broken images (Bad CRC-32) that python-docx/docling can't open.
    """
    try:
        with zipfile.ZipFile(docx_path) as z:
            data = z.read("word/document.xml")
        root = ET.fromstring(data)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs = root.findall(".//w:p", ns)
        lines = []
        for p in paragraphs:
            texts = p.findall(".//w:t", ns)
            line = "".join(t.text for t in texts if t.text)
            lines.append(line)
        return "\n\n".join(lines)
    except Exception:
        return None


def _is_image_only_pdf(text: str) -> bool:
    """Detect PDFs that produced no real text (only image placeholders or empty)."""
    stripped = text.strip()
    if not stripped:
        return True
    # Remove all <!-- image --> placeholders and check if anything remains
    import re
    no_images = re.sub(r"<!--\s*image\s*-->", "", stripped).strip()
    return len(no_images) < 50


def batch_convert_to_files(
    directory: str,
    extensions: Optional[list[str]] = None,
    output_format: Literal["markdown", "json", "html"] = "markdown",
    enable_ocr: bool = False,
    skip_existing: bool = True,
    skip_image_only: bool = True,
) -> dict:
    """
    Batch convert all PDF/DOCX files in a directory to corresponding output files.

    Key features:
    - Disables OCR by default for speed (text-based PDFs don't need OCR)
    - Skips files that already have non-empty output (incremental processing)
    - Detects and skips image-only PDFs
    - Falls back to direct XML parsing for corrupted DOCX files
    - Handles non-ASCII filenames on Windows

    Args:
        directory: Directory containing source files
        extensions: File extensions to process (default: [".pdf", ".docx"])
        output_format: Output format
        enable_ocr: Enable OCR for scanned documents
        skip_existing: Skip files that already have non-empty output files
        skip_image_only: Skip and report image-only PDFs

    Returns:
        Dict with 'converted', 'skipped', 'failed' lists and summary stats
    """
    _fix_stdout_encoding()

    if extensions is None:
        extensions = [".pdf", ".docx"]

    # Collect all source files
    all_files = []
    for ext in extensions:
        all_files.extend(glob.glob(os.path.join(directory, f"*{ext}")))
    all_files = sorted(all_files)

    if not all_files:
        print(f"No files found in {directory} with extensions {extensions}")
        return {"converted": [], "skipped": [], "failed": [], "total": 0}

    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions

    # Disable OCR by default for speed
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = enable_ocr
    pipeline_options.do_table_structure = False

    converter = DocumentConverter(
        format_options={"pdf": PdfFormatOption(pipeline_options=pipeline_options)}
    )

    converted = []
    skipped = []
    failed = []

    for i, filepath in enumerate(all_files, 1):
        basename = os.path.splitext(os.path.basename(filepath))[0]
        out_ext = ".md" if output_format == "markdown" else (".html" if output_format == "html" else ".json")
        outpath = os.path.join(directory, basename + out_ext)
        fname = os.path.basename(filepath).replace("\xa0", " ")

        # Skip already-converted files
        if skip_existing and os.path.exists(outpath) and os.path.getsize(outpath) > 100:
            print(f"[{i}/{len(all_files)}] SKIP (already done): {fname}")
            skipped.append({"file": filepath, "reason": "already_converted"})
            continue

        print(f"[{i}/{len(all_files)}] Converting: {fname}", flush=True)

        try:
            result = converter.convert(filepath)

            if output_format == "markdown":
                content = result.document.export_to_markdown()
            elif output_format == "html":
                content = result.document.export_to_html()
            elif output_format == "json":
                content = json.dumps(result.document.export_to_dict(), indent=2, ensure_ascii=False)

            # Check for image-only PDFs
            if skip_image_only and filepath.lower().endswith(".pdf") and _is_image_only_pdf(content):
                print(f"  -> SKIP (image-only PDF, no extractable text)")
                skipped.append({"file": filepath, "reason": "image_only"})
                continue

            with open(outpath, "w", encoding="utf-8") as f:
                f.write(content)

            print(f"  -> OK ({len(content)} chars)")
            converted.append({"file": filepath, "output": outpath, "chars": len(content)})

        except Exception as e:
            err_msg = str(e)

            # Fallback for corrupted DOCX
            if filepath.lower().endswith(".docx"):
                print(f"  -> Docling failed, trying direct XML extraction...")
                fallback = _convert_corrupted_docx(filepath)
                if fallback and len(fallback.strip()) > 50:
                    with open(outpath, "w", encoding="utf-8") as f:
                        f.write(fallback)
                    print(f"  -> OK via fallback ({len(fallback)} chars)")
                    converted.append({"file": filepath, "output": outpath, "chars": len(fallback), "fallback": True})
                    continue

            print(f"  -> FAILED: {err_msg}")
            failed.append({"file": filepath, "error": err_msg})

    summary = f"\n=== Done: {len(converted)} converted, {len(skipped)} skipped, {len(failed)} failed ==="
    print(summary)

    return {
        "converted": converted,
        "skipped": skipped,
        "failed": failed,
        "total": len(all_files),
    }


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Docling document converter wrapper")
    parser.add_argument("source", help="Document path/URL, or directory for --batch mode")
    parser.add_argument("-f", "--format", choices=["markdown", "json", "html"],
                        default="markdown", help="Output format")
    parser.add_argument("--ocr", action="store_true", help="Enable OCR")
    parser.add_argument("-o", "--output", help="Output file path (single file mode)")
    parser.add_argument("--batch", action="store_true",
                        help="Batch mode: convert all PDF/DOCX in directory")
    parser.add_argument("--no-skip-existing", action="store_true",
                        help="Re-convert files that already have output")

    args = parser.parse_args()

    if args.batch:
        batch_convert_to_files(
            directory=args.source,
            output_format=args.format,
            enable_ocr=args.ocr,
            skip_existing=not args.no_skip_existing,
        )
    else:
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
