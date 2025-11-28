import requests
import os

def test_generate_endpoint():
    url = "http://127.0.0.1:8080/generate"
    
    # Prepare the file
    file_path = "test_rich.pdf"
    
    with open(file_path, "rb") as f:
        files = {"file": ("test_rich.pdf", f, "application/pdf")}
        data = {
            "slide_count": 6,
            "include_visuals": True,
            "store": False
        }
        
        try:
            response = requests.post(url, files=files, data=data)
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {response.headers}")
            
            if response.status_code == 200:
                # Save the PPTX file
                with open("output_test.pptx", "wb") as output_file:
                    output_file.write(response.content)
                print("✅ Presentation generated successfully! Saved as output_test.pptx")
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_generate_endpoint()