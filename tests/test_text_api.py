import requests

def test_text_endpoint():
    """Test the API with a simple text input to verify the core functionality works"""
    
    # Let's create a simple text-based test by modifying our approach
    # We'll use the existing /generate endpoint but create a temporary file
    
    # Create a temporary text file with sufficient content
    test_content = """This is a comprehensive test document for presentation generation. 
    It contains enough text content to meet the minimum requirements for AI-powered 
    presentation creation. The document discusses various topics including technology, 
    business strategies, and market analysis. This content will be used to generate a 
    professional presentation with multiple slides covering different aspects of the 
    subject matter. The goal is to create an engaging and informative presentation 
    that can be used for educational or business purposes. Additional content is added 
    here to ensure we have sufficient text for the AI model to work with effectively."""
    
    # Write to a temporary file
    with open("temp_test.txt", "w", encoding="utf-8") as f:
        f.write(test_content)
    
    url = "http://127.0.0.1:8000/generate"
    
    with open("temp_test.txt", "rb") as f:
        files = {"file": ("temp_test.txt", f, "text/plain")}
        data = {
            "slide_count": 6,
            "include_visuals": True,
            "store": False
        }
        
        try:
            response = requests.post(url, files=files, data=data)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                # Save the PPTX file
                with open("output_test.pptx", "wb") as output_file:
                    output_file.write(response.content)
                print("✅ Presentation generated successfully! Saved as output_test.pptx")
                print(f"Response: {response.json() if response.headers.get('content-type') == 'application/json' else 'File response'}")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
    
    # Clean up
    import os
    if os.path.exists("temp_test.txt"):
        os.remove("temp_test.txt")

if __name__ == "__main__":
    test_text_endpoint()