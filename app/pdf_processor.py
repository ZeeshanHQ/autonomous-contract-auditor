import fitz  # PyMuPDF
import io

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extracts text from PDF bytes."""
    text = ""
    try:
        # Open PDF from bytes
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        for page in doc:
            text += page.get_text()
            
        doc.close()
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        
    return text.strip()
