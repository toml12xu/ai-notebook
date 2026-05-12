---
name: docling
description: Document processing and conversion for gen AI. Parses PDF, DOCX, PPTX, XLSX, HTML, images, and audio. Exports to Markdown, JSON, HTML. Includes enhanced DOCX converter with LaTeX equation support and image extraction.
github_url: https://github.com/docling-project/docling
github_hash: 6f205ae2119fe694abaf200df5662837b3854f53
version: 2.70.1
created_at: 2026-01-29T10:58:00
updated_at: 2026-01-29T12:00:00
entry_point: scripts/wrapper.py
dependencies:
  - docling
  - docling-core
---

# Docling Skill

Document processing toolkit that parses diverse formats and provides seamless integration with gen AI workflows.

## When to Use

Use this skill when the user needs to:
- Convert PDF, DOCX, PPTX, XLSX, HTML documents to Markdown or structured JSON
- Extract text, tables, and structured content from documents
- Process scanned PDFs or images with OCR
- Prepare documents for RAG (Retrieval-Augmented Generation) pipelines
- Extract structured information from documents

## Supported Formats

**Input formats:**
- PDF (including scanned with OCR)
- DOCX (Word documents)
- PPTX (PowerPoint presentations)
- XLSX (Excel spreadsheets)
- HTML/XHTML
- Images (PNG, JPEG, TIFF, BMP, GIF)
- Audio (WAV, MP3) with ASR
- WebVTT (subtitle files)

**Output formats:**
- Markdown
- JSON (lossless DoclingDocument format)
- HTML
- DocTags (structured XML-like format)

## Installation

```bash
pip install docling
```

> Requires Python 3.10 or higher

## Quick Usage

### Python API (Recommended)

```python
from docling.document_converter import DocumentConverter

# Convert from URL or local path
converter = DocumentConverter()
result = converter.convert("path/to/document.pdf")

# Export to Markdown
markdown = result.document.export_to_markdown()

# Export to JSON (lossless)
json_output = result.document.export_to_dict()
```

### CLI

```bash
# Basic conversion
docling document.pdf

# Specify output format
docling document.pdf --output markdown

# Use VLM for enhanced understanding
docling --pipeline vlm --vlm-model granite_docling document.pdf
```

## Wrapper Script Usage

The skill provides a wrapper script at `scripts/wrapper.py` for common operations:

```python
from docling_skill.wrapper import convert_document, batch_convert

# Single document conversion
result = convert_document(
    source="path/to/document.pdf",
    output_format="markdown"  # "markdown", "json", "html"
)

# Batch conversion
results = batch_convert(
    sources=["doc1.pdf", "doc2.docx", "https://example.com/doc.pdf"],
    output_format="markdown"
)
```

## Advanced Features

### Table Extraction

Docling excels at table structure recognition:

```python
from docling.document_converter import DocumentConverter

converter = DocumentConverter()
result = converter.convert("document.pdf")

# Access tables
for table in result.document.tables:
    # Export table to pandas DataFrame
    df = table.export_to_dataframe()
    print(df)
```

### OCR for Scanned Documents

```python
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions

# Enable OCR
pipeline_options = PdfPipelineOptions()
pipeline_options.do_ocr = True

converter = DocumentConverter(
    format_options={
        "pdf": PdfFormatOption(pipeline_options=pipeline_options)
    }
)
result = converter.convert("scanned_document.pdf")
```

### Structured Information Extraction (Beta)

```python
from docling.document_converter import DocumentConverter
from pydantic import BaseModel

class Invoice(BaseModel):
    invoice_number: str
    date: str
    total: float
    items: list[dict]

converter = DocumentConverter()
result = converter.convert("invoice.pdf")

# Extract structured data
extracted = result.document.extract(Invoice)
```

## Integration with AI Frameworks

### LangChain

```python
from langchain_community.document_loaders import DoclingLoader

loader = DoclingLoader(file_path="document.pdf")
docs = loader.load()
```

### LlamaIndex

```python
from llama_index.readers.docling import DoclingReader

reader = DoclingReader()
documents = reader.load_data(file_path="document.pdf")
```

## Best Practices

1. **For large documents**: Use batch processing with `converter.convert_all()`
2. **For scanned PDFs**: Always enable OCR in pipeline options
3. **For RAG pipelines**: Export to Markdown for best chunking results
4. **For data extraction**: Use the JSON export to preserve document structure

## Troubleshooting

### Memory Issues with Large PDFs
```python
# Process pages in chunks
pipeline_options = PdfPipelineOptions()
pipeline_options.images_scale = 1.0  # Reduce from default 2.0
```

### OCR Language Support
```python
# Specify OCR languages
pipeline_options = PdfPipelineOptions()
pipeline_options.ocr_options.lang = ["en", "de", "fr"]
```

## Enhanced DOCX Converter (LaTeX + Images)

When docling's default DOCX conversion fails on documents with complex mathematical equations (OMML format), use the enhanced converter that provides:

1. **OMML to LaTeX conversion** - Office Math equations converted to LaTeX format
2. **Image extraction** - Embedded images extracted and properly referenced in markdown

### When to Use the Enhanced Converter

Use `scripts/docx_latex_converter.py` when:
- Docling fails with "Pipeline SimplePipeline failed" on DOCX files
- Your document contains mathematical equations (Office Math/OMML format)
- You need images extracted and displayed in the markdown output

### Quick Usage

```python
from scripts.docx_latex_converter import convert_docx_to_markdown

# Basic conversion - images extracted to ./images/
markdown = convert_docx_to_markdown("document.docx", "output.md")

# Custom image directory
markdown = convert_docx_to_markdown(
    "document.docx",
    "output.md",
    image_dir="assets/images"
)
```

### CLI Usage

```bash
python scripts/docx_latex_converter.py document.docx output.md [image_dir]
```

### Output Format

**Equations:**
- Display equations: `$$\frac{a}{b}$$`
- Inline equations: `$x^2 + y^2 = z^2$`

**Images:**
- Extracted to specified directory (default: `images/`)
- Referenced in markdown: `![Description](images/image1.png)`

### Supported Math Elements

| OMML Element | LaTeX Output |
|-------------|--------------|
| Fractions | `\frac{num}{den}` |
| Square roots | `\sqrt{x}`, `\sqrt[n]{x}` |
| Superscripts | `x^{2}` |
| Subscripts | `x_{i}` |
| Summations | `\sum_{i=0}^{n}` |
| Integrals | `\int_{a}^{b}` |
| Matrices | `\begin{matrix}...\end{matrix}` |
| Greek letters | `\alpha`, `\beta`, `\gamma`, etc. |
| Accents | `\hat{x}`, `\bar{x}`, `\vec{x}` |
| Delimiters | `\left( ... \right)` |

### Supported Image Formats

| Format | Display Support |
|--------|----------------|
| PNG | ✅ Universal |
| JPG/JPEG | ✅ Universal |
| GIF | ✅ Universal |
| WMF | ⚠️ Windows only |
| EMF | ⚠️ Windows only |

> **Note:** WMF/EMF (Windows Metafile) formats may not display in all markdown viewers. Consider converting them to PNG if cross-platform support is needed.

### Fallback Strategy

```python
def convert_document(docx_path, output_path):
    """Try docling first, fall back to enhanced converter."""
    try:
        from docling.document_converter import DocumentConverter
        converter = DocumentConverter()
        result = converter.convert(docx_path)
        return result.document.export_to_markdown()
    except Exception:
        # Docling failed - use enhanced converter
        from scripts.docx_latex_converter import convert_docx_to_markdown
        return convert_docx_to_markdown(docx_path, output_path)
```

## Resources

- [Documentation](https://docling-project.github.io/docling/)
- [Examples](https://docling-project.github.io/docling/examples/)
- [Technical Report](https://arxiv.org/abs/2408.09869)
- [GitHub Repository](https://github.com/docling-project/docling)
