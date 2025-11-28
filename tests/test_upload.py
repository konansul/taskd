from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os

app = FastAPI()

@app.post("/test-upload")
async def test_upload(file: UploadFile = File(...)):
    """Test file upload without AI processing"""
    try:
        suffix = os.path.splitext(file.filename)[1]
        tmp_path = os.path.join(tempfile.gettempdir(), f"upload_test_{os.getpid()}{suffix}")
        content = await file.read()
        
        with open(tmp_path, "wb") as f:
            f.write(content)
        
        print(f"File uploaded successfully: {tmp_path}")
        print(f"File size: {len(content)} bytes")
        
        # Test reading the file
        from docx import Document
        import pdfplumber
        
        ext = os.path.splitext(tmp_path)[1].lower()
        text = ""
        
        if ext == '.docx':
            try:
                doc = Document(tmp_path)
                text = '\n'.join([para.text for para in doc.paragraphs if para.text.strip()])
                print(f"DOCX text length: {len(text)}")
            except Exception as e:
                print(f"DOCX error: {e}")
        elif ext == '.pdf':
            try:
                with pdfplumber.open(tmp_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text.strip() + '\n'
                print(f"PDF text length: {len(text)}")
            except Exception as e:
                print(f"PDF error: {e}")
        
        # Clean up
        os.remove(tmp_path)
        
        return JSONResponse(content={
            "message": "File processed successfully",
            "filename": file.filename,
            "file_size": len(content),
            "text_length": len(text),
            "text_preview": text[:200] if text else "No text extracted"
        })
        
    except Exception as e:
        print(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

@app.get("/health")
def health():
    return {"status": "ok"}