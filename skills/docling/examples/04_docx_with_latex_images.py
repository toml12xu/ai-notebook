"""
Example: Convert DOCX with LaTeX equations and images.

This example demonstrates the enhanced DOCX converter that handles:
1. Office Math (OMML) equations -> LaTeX format
2. Embedded images -> extracted and referenced in markdown

Use this when docling's default conversion fails on complex math documents.
"""
from pathlib import Path

# Import the enhanced converter
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
from docx_latex_converter import convert_docx_to_markdown, DocxToMarkdown, OmmlToLatex


def example_basic_conversion():
    """Basic conversion of a DOCX file to Markdown."""
    
    # Convert a document - images go to ./images/ by default
    markdown = convert_docx_to_markdown(
        input_path="document.docx",
        output_path="document.md"
    )
    
    print(f"Conversion complete: {len(markdown)} characters")


def example_custom_image_directory():
    """Conversion with custom image output directory."""
    
    markdown = convert_docx_to_markdown(
        input_path="document.docx",
        output_path="output/document.md",
        image_dir="output/assets/images"
    )
    
    # Images will be extracted to output/assets/images/
    # Markdown will reference them as: ![alt](assets/images/image1.png)


def example_programmatic_access():
    """Access the converter programmatically for more control."""
    
    # Create converter instance
    converter = DocxToMarkdown(
        docx_path="document.docx",
        image_dir="extracted_images"
    )
    
    # Convert and get markdown
    markdown = converter.convert()
    
    # Access conversion statistics
    print(f"Images extracted: {converter.image_counter}")
    print(f"Image mappings: {converter.extracted_images}")
    
    return markdown


def example_latex_only():
    """Convert just an OMML equation element to LaTeX."""
    import xml.etree.ElementTree as ET
    
    # Example OMML XML for a fraction
    omml_xml = '''
    <m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">
        <m:f>
            <m:num><m:r><m:t>a</m:t></m:r></m:num>
            <m:den><m:r><m:t>b</m:t></m:r></m:den>
        </m:f>
    </m:oMath>
    '''
    
    # Parse and convert
    elem = ET.fromstring(omml_xml)
    converter = OmmlToLatex()
    latex = converter.convert(elem)
    
    print(f"LaTeX output: {latex}")
    # Output: \frac{a}{b}


def example_with_docling_fallback():
    """Try docling first, fall back to enhanced converter if it fails."""
    from pathlib import Path
    
    docx_path = "document.docx"
    output_path = "document.md"
    
    try:
        # Try docling first
        from docling.document_converter import DocumentConverter
        
        converter = DocumentConverter()
        result = converter.convert(docx_path)
        markdown = result.document.export_to_markdown()
        
        Path(output_path).write_text(markdown, encoding='utf-8')
        print("Converted with docling")
        
    except Exception as e:
        print(f"Docling failed: {e}")
        print("Falling back to enhanced converter...")
        
        # Fall back to enhanced converter
        markdown = convert_docx_to_markdown(docx_path, output_path)
        print("Converted with enhanced converter")
    
    return markdown


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python 04_docx_with_latex_images.py <input.docx> [output.md]")
        print("\nThis will convert the DOCX with LaTeX equations and extract images.")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else input_file.replace('.docx', '.md')
    
    convert_docx_to_markdown(input_file, output_file)
