from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import tempfile
import os
import json

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use system environment variables

from backend.utils.file_reader import read_file
from backend.utils.prompt import get_presentation as build_presentation_from_text, generate_image_hf
from backend.utils.slide import parse_gpt_response, generate_pptx
from backend.utils.storage import (
    save_presentation, load_presentation, update_presentation,
    delete_presentation, list_presentations, generate_presentation_id
)
from backend.utils.pdf_export import create_pdf_from_slides

app = FastAPI(
    title="Presentation Assistant API",
    version="2.0.0",
    description="API for generating, editing, and exporting AI-powered presentations"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class SlideUpdate(BaseModel):
    slides: List[Dict]


class SlideReorder(BaseModel):
    slide_indices: List[int]


class ImageGenerationRequest(BaseModel):
    description: str
    slide_title: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok", "message": "Presentation Assistant API is running"}


@app.post("/generate")
async def generate_presentation(
    file: UploadFile = File(..., description="PDF or DOCX file"),
    slide_count: int = Form(6, description="Total number of slides"),
    include_visuals: bool = Form(False, description="Whether to include visuals as slides"),
    store: bool = Form(True, description="Whether to store the presentation for later editing")
):
    """
    Generate a presentation from an uploaded document.
    Returns the presentation ID and optionally the PPTX file.
    """
    try:
        suffix = os.path.splitext(file.filename)[1]
        tmp_path = os.path.join(tempfile.gettempdir(), f"upload_{os.getpid()}{suffix}")
        content = await file.read()
        with open(tmp_path, "wb") as f:
            f.write(content)
        print(f"Wrote {len(content)} bytes to {tmp_path}")

        document_text = read_file(tmp_path)
        # Keep temp file for debugging
        print(f"Temp file kept at: {tmp_path}")

        # Validate extracted text
        if not document_text or len(document_text.strip()) < 50:
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from the document. The document might contain only images or be corrupted."
            )
        
        # Generate presentation using AI
        try:
            gpt_response = build_presentation_from_text(
                document_text,
                slide_count=slide_count,
                include_visuals=include_visuals
            )
        except ValueError as ve:
            # Handle API errors or other value errors
            error_msg = str(ve)
            if "API Error" in error_msg:
                raise HTTPException(
                    status_code=500,
                    detail=f"AI API error: {error_msg}. Please check your GOOGLE_API_KEY configuration."
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error generating presentation: {error_msg}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error during presentation generation: {str(e)}"
            )
        
        # Parse the response
        try:
            slides = parse_gpt_response(gpt_response)
        except ValueError as ve:
            error_msg = str(ve)
            if "Invalid JSON format" in error_msg:
                raise HTTPException(
                    status_code=500,
                    detail=f"JSON parsing error: {error_msg}. The AI response may be malformed. Please try again with a smaller document or fewer slides."
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Error parsing AI response: {error_msg}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error parsing response: {str(e)}"
            )

        # Store presentation if requested
        presentation_id = None
        if store:
            presentation_id = generate_presentation_id()
            saved_presentation = save_presentation(
                presentation_id,
                slides,
                metadata={
                    "original_filename": file.filename,
                    "slide_count": slide_count,
                    "include_visuals": include_visuals,
                    "source_text_length": len(document_text)
                }
            )
            presentation_id = saved_presentation["id"]

        # Generate PPTX file
        output_filename = f"generated_presentation_{presentation_id or 'temp'}.pptx"
        generate_pptx(slides, output_filename)

        response_data = {
            "presentation_id": presentation_id,
            "slide_count": len(slides),
            "message": "Presentation generated successfully"
        }

        if presentation_id:
            return JSONResponse(content=response_data)
        else:
            # Return file if not storing
            return FileResponse(
                path=output_filename,
                media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                filename=output_filename
            )

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating presentation: {str(e)}")


@app.get("/presentations")
def get_all_presentations():
    """Get list of all stored presentations."""
    try:
        presentations = list_presentations()
        return {"presentations": presentations, "count": len(presentations)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/presentations/{presentation_id}")
def get_presentation(presentation_id: str):
    """Get a specific presentation by ID."""
    presentation = load_presentation(presentation_id)
    if presentation is None:
        raise HTTPException(status_code=404, detail="Presentation not found")
    return presentation


@app.put("/presentations/{presentation_id}")
def update_presentation_endpoint(presentation_id: str, slide_update: SlideUpdate):
    """Update slides in a presentation."""
    existing = load_presentation(presentation_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Presentation not found")
    
    try:
        # Validate slides structure
        for slide in slide_update.slides:
            slide_type = slide.get("type")
            if slide_type not in {"title", "intro", "main", "recommendation"}:
                raise ValueError(f"Invalid slide type: {slide_type}")
        
        updated = update_presentation(presentation_id, slide_update.slides)
        return {
            "message": "Presentation updated successfully",
            "presentation": updated
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/presentations/{presentation_id}/reorder")
def reorder_slides(presentation_id: str, reorder: SlideReorder):
    """Reorder slides in a presentation."""
    presentation = load_presentation(presentation_id)
    if presentation is None:
        raise HTTPException(status_code=404, detail="Presentation not found")
    
    slides = presentation["slides"]
    if len(reorder.slide_indices) != len(slides):
        raise HTTPException(
            status_code=400,
            detail=f"Expected {len(slides)} indices, got {len(reorder.slide_indices)}"
        )
    
    # Validate indices
    if set(reorder.slide_indices) != set(range(len(slides))):
        raise HTTPException(status_code=400, detail="Invalid slide indices")
    
    # Reorder slides
    reordered_slides = [slides[i] for i in reorder.slide_indices]
    updated = update_presentation(presentation_id, reordered_slides)
    
    return {
        "message": "Slides reordered successfully",
        "presentation": updated
    }


@app.delete("/presentations/{presentation_id}")
def delete_presentation_endpoint(presentation_id: str):
    """Delete a presentation."""
    if delete_presentation(presentation_id):
        return {"message": "Presentation deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Presentation not found")


@app.get("/presentations/{presentation_id}/export/pptx")
def export_pptx(presentation_id: str):
    """Export presentation as PowerPoint file."""
    presentation = load_presentation(presentation_id)
    if presentation is None:
        raise HTTPException(status_code=404, detail="Presentation not found")
    
    try:
        slides = presentation["slides"]
        output_filename = f"presentation_{presentation_id}.pptx"
        generate_pptx(slides, output_filename)
        
        return FileResponse(
            path=output_filename,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=output_filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting PPTX: {str(e)}")


@app.post("/presentations/{presentation_id}/export/pdf")
def export_pdf(presentation_id: str):
    """Export presentation as PDF file."""
    presentation = load_presentation(presentation_id)
    if presentation is None:
        raise HTTPException(status_code=404, detail="Presentation not found")
    
    try:
        slides = presentation["slides"]
        output_filename = f"presentation_{presentation_id}.pdf"
        create_pdf_from_slides(slides, output_filename)
        
        return FileResponse(
            path=output_filename,
            media_type="application/pdf",
            filename=output_filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting PDF: {str(e)}")


@app.post("/presentations/{presentation_id}/slides/{slide_index}/image")
async def generate_slide_image(presentation_id: str, slide_index: int, request: ImageGenerationRequest):
    """Generate an image for a specific slide."""
    presentation = load_presentation(presentation_id)
    if presentation is None:
        raise HTTPException(status_code=404, detail="Presentation not found")
    
    slides = presentation["slides"]
    if slide_index < 0 or slide_index >= len(slides):
        raise HTTPException(status_code=400, detail="Invalid slide index")
    
    slide = slides[slide_index]
    
    # Use provided description or generate from slide content
    if request.description:
        description = request.description
    else:
        # Generate description from slide content
        if slide.get("type") == "main":
            description = f"{slide.get('title', '')}: {', '.join([slide.get(f'point{i}', '') for i in range(1, 5) if slide.get(f'point{i}')])}"
        else:
            description = str(slide.get("title", "Presentation slide"))
    
    try:
        # Translate to English for image generation
        from googletrans import Translator
        translator = Translator()
        translated = translator.translate(description, src='az', dest='en')
        english_description = translated.text
        
        # Generate image
        image_filename = f"slide_image_{presentation_id}_{slide_index}.png"
        image_path = generate_image_hf(english_description, image_filename)
        
        if image_path and os.path.exists(image_path):
            # Update slide visual
            if slide.get("type") == "main":
                if "visual" not in slide:
                    slide["visual"] = {}
                slide["visual"]["type"] = "image"
                slide["visual"]["description"] = description
                slide["visual"]["image_path"] = image_path
            
            # Update presentation
            update_presentation(presentation_id, slides)
            
            return {
                "message": "Image generated successfully",
                "image_path": image_path,
                "slide_index": slide_index
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to generate image")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")


@app.get("/templates")
def get_templates():
    """Get available presentation templates."""
    templates = [
        {
            "id": "default",
            "name": "Default Template",
            "description": "Standard presentation template",
            "file": "format_new.pptx"
        }
    ]
    
    # Check if template file exists
    template_dir = os.path.dirname(os.path.abspath(__file__))
    for template in templates:
        template_path = os.path.join(template_dir, template["file"])
        template["available"] = os.path.exists(template_path)
    
    return {"templates": templates}


@app.post("/presentations/{presentation_id}/slides/{slide_index}")
def update_single_slide(presentation_id: str, slide_index: int, slide_data: Dict = Body(...)):
    """Update a single slide in the presentation."""
    presentation = load_presentation(presentation_id)
    if presentation is None:
        raise HTTPException(status_code=404, detail="Presentation not found")
    
    slides = presentation["slides"]
    if slide_index < 0 or slide_index >= len(slides):
        raise HTTPException(status_code=400, detail="Invalid slide index")
    
    # Validate slide type
    slide_type = slide_data.get("type")
    if slide_type not in {"title", "intro", "main", "recommendation"}:
        raise HTTPException(status_code=400, detail=f"Invalid slide type: {slide_type}")
    
    # Update the slide
    slides[slide_index] = slide_data
    updated = update_presentation(presentation_id, slides)
    
    return {
        "message": "Slide updated successfully",
        "slide": slide_data,
        "slide_index": slide_index
    }


@app.get("/presentations/{presentation_id}/slides/{slide_index}")
def get_single_slide(presentation_id: str, slide_index: int):
    """Get a single slide from the presentation."""
    presentation = load_presentation(presentation_id)
    if presentation is None:
        raise HTTPException(status_code=404, detail="Presentation not found")
    
    slides = presentation["slides"]
    if slide_index < 0 or slide_index >= len(slides):
        raise HTTPException(status_code=400, detail="Invalid slide index")
    
    return {
        "slide": slides[slide_index],
        "slide_index": slide_index,
        "total_slides": len(slides)
    }


@app.post("/presentations/{presentation_id}/generate-all-images")
async def generate_all_slide_images(presentation_id: str):
    """Generate images for all slides that need them (main slides with image visuals)."""
    presentation = load_presentation(presentation_id)
    if presentation is None:
        raise HTTPException(status_code=404, detail="Presentation not found")
    
    slides = presentation["slides"]
    generated_images = []
    errors = []
    
    from googletrans import Translator
    translator = Translator()
    
    for idx, slide in enumerate(slides):
        if slide.get("type") == "main":
            visual = slide.get("visual", {})
            if visual.get("type") == "image":
                try:
                    # Generate description from slide content
                    title = slide.get("title", "")
                    points = [slide.get(f"point{i}", "") for i in range(1, 5) if slide.get(f"point{i}")]
                    description = f"{title}: {', '.join(points[:2])}" if points else title
                    
                    # Translate to English
                    translated = translator.translate(description, src='az', dest='en')
                    english_description = translated.text
                    
                    # Generate image
                    image_filename = f"slide_image_{presentation_id}_{idx}.png"
                    image_path = generate_image_hf(english_description, image_filename)
                    
                    if image_path and os.path.exists(image_path):
                        visual["image_path"] = image_path
                        visual["description"] = description
                        generated_images.append({
                            "slide_index": idx,
                            "image_path": image_path,
                            "description": description
                        })
                    else:
                        errors.append(f"Failed to generate image for slide {idx}")
                except Exception as e:
                    errors.append(f"Error generating image for slide {idx}: {str(e)}")
    
    # Update presentation with image paths
    update_presentation(presentation_id, slides)
    
    return {
        "message": f"Generated {len(generated_images)} images",
        "generated_images": generated_images,
        "errors": errors
    }
