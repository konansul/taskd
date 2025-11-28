import requests
import os
from fpdf import FPDF

def create_test_pdf():
    """Create a test PDF with sufficient content"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    content = """This is a comprehensive test document for presentation generation. 
    It contains enough text content to meet the minimum requirements for AI-powered 
    presentation creation. The document discusses various topics including technology, 
    business strategies, and market analysis. This content will be used to generate a 
    professional presentation with multiple slides covering different aspects of the 
    subject matter. The goal is to create an engaging and informative presentation 
    that can be used for educational or business purposes. Additional content is added 
    here to ensure we have sufficient text for the AI model to work with effectively."""
    
    # Split content into lines that fit on page
    lines = content.split('\n')
    for line in lines:
        pdf.cell(200, 10, txt=line.strip(), ln=1)
    
    pdf.output("test_rich.pdf")
    print("Created test_rich.pdf")

def test_pdf_endpoint():
    """Test the API with a rich PDF file"""
    
    # Create the test PDF first
    create_test_pdf()
    
    # Check if file was created and has content
    if not os.path.exists("test_rich.pdf"):
        print("❌ Test PDF not created")
        return
    
    url = "http://127.0.0.1:8000/generate"
    
    with open("test_rich.pdf", "rb") as f:
        files = {"file": ("test_rich.pdf", f, "application/pdf")}
        data = {
            "slide_count": 6,
            "include_visuals": True,
            "store": False
        }
        
        try:
            response = requests.post(url, files=files, data=data)
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                # Check if it's a file response or JSON
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    print("✅ JSON Response:", response.json())
                else:
                    # Save the PPTX file
                    with open("output_test.pptx", "wb") as output_file:
                        output_file.write(response.content)
                    print("✅ Presentation generated successfully! Saved as output_test.pptx")
                    print(f"File size: {len(response.content)} bytes")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_pdf_endpoint()