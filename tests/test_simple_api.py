import requests
import time

def test_simple_pdf():
    """Test with a simple request and timeout"""
    
    url = "http://127.0.0.1:8080/generate"
    
    # Use the existing test_rich.pdf
    try:
        with open("test_rich.pdf", "rb") as f:
            files = {"file": ("test_rich.pdf", f, "application/pdf")}
            data = {
                "slide_count": 3,  # Reduce slide count to make it faster
                "include_visuals": False,  # Disable visuals for faster processing
                "store": False
            }
            
            print("Sending request...")
            start_time = time.time()
            
            response = requests.post(url, files=files, data=data, timeout=60)  # 60 second timeout
            
            end_time = time.time()
            print(f"Request completed in {end_time - start_time:.2f} seconds")
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                print(f"Content-Type: {content_type}")
                
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
                
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 60 seconds")
    except Exception as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_simple_pdf()