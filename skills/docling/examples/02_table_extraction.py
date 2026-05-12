"""
Table Extraction with Docling

Docling excels at recognizing and extracting tables from documents.
This example shows how to extract tables to pandas DataFrames.
"""

from docling.document_converter import DocumentConverter


def extract_tables_from_pdf(pdf_path: str):
    """
    Extract all tables from a PDF and convert to pandas DataFrames.
    
    Args:
        pdf_path: Path to PDF file or URL
        
    Returns:
        List of pandas DataFrames, one per table
    """
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    
    dataframes = []
    for i, table in enumerate(result.document.tables):
        try:
            df = table.export_to_dataframe()
            print(f"Table {i+1}: {df.shape[0]} rows x {df.shape[1]} columns")
            dataframes.append(df)
        except Exception as e:
            print(f"Table {i+1}: Could not convert - {e}")
    
    return dataframes


def tables_to_csv(pdf_path: str, output_dir: str = "."):
    """
    Extract tables and save each as a CSV file.
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save CSV files
    """
    from pathlib import Path
    
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    for i, table in enumerate(result.document.tables):
        try:
            df = table.export_to_dataframe()
            csv_path = output_path / f"table_{i+1}.csv"
            df.to_csv(csv_path, index=False)
            print(f"Saved: {csv_path}")
        except Exception as e:
            print(f"Table {i+1}: Could not save - {e}")


def tables_to_json(pdf_path: str):
    """
    Extract tables as JSON-serializable dictionaries.
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        List of tables as dictionaries
    """
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    
    tables_json = []
    for i, table in enumerate(result.document.tables):
        try:
            df = table.export_to_dataframe()
            tables_json.append({
                "table_index": i,
                "num_rows": len(df),
                "num_cols": len(df.columns),
                "columns": list(df.columns),
                "data": df.to_dict(orient="records")
            })
        except Exception as e:
            tables_json.append({
                "table_index": i,
                "error": str(e)
            })
    
    return tables_json


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        print(f"Extracting tables from: {pdf_path}")
        dfs = extract_tables_from_pdf(pdf_path)
        
        for i, df in enumerate(dfs):
            print(f"\n--- Table {i+1} ---")
            print(df.head())
    else:
        print("Usage: python 02_table_extraction.py <pdf_path>")
