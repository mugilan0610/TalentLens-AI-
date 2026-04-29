import streamlit as st
import pdfplumber
import docx
import io

@st.cache_data(show_spinner=False)
def extract_text_from_file(file_bytes, filename):
    """Extracts text from PDF, DOCX, or TXT files."""
    try:
        if filename.lower().endswith('.pdf'):
            text = ""
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            return text
        elif filename.lower().endswith('.docx'):
            doc = docx.Document(io.BytesIO(file_bytes))
            return "\n".join([para.text for para in doc.paragraphs])
        elif filename.lower().endswith('.doc'):
            import re
            text = file_bytes.decode('utf-8', errors='ignore')
            text = re.sub(r'[^\x20-\x7E\n\t]+', ' ', text)
            return text
        elif filename.lower().endswith('.txt'):
            return file_bytes.decode('utf-8')
        else:
            return None
    except Exception as e:
        return f"ERROR: {str(e)}"
