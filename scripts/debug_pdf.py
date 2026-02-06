
import os
import sys
import django
from langchain_community.document_loaders import PyPDFLoader
import tempfile

# Setup Django environment to use the same settings
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_pdf_extraction(file_path):
    print(f"Testing PDF extraction for: {file_path}")
    if not os.path.exists(file_path):
        print("File does not exist.")
        return

    try:
        loader = PyPDFLoader(file_path)
        pages = loader.load()
        text = "\n\n".join([p.page_content for p in pages])
        print(f"SUCCESS: Extracted {len(text)} characters from {len(pages)} pages.")
        print("Preview:")
        print(text[:200])
    except Exception as e:
        print(f"FAILURE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Test with the generated verification file
    test_pdf_extraction("test_docs/verification_test.pdf")
