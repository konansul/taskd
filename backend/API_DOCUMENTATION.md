# Presentation Assistant API Documentation

## Overview

The Presentation Assistant API provides endpoints for generating, editing, and exporting AI-powered presentations from uploaded documents (PDF/DOCX).

## Base URL

```
http://localhost:8000
```

## Endpoints

### Health Check

#### `GET /health`
Check if the API is running.

**Response:**
```json
{
  "status": "ok",
  "message": "Presentation Assistant API is running"
}
```

---

### Generate Presentation

#### `POST /generate`
Generate a presentation from an uploaded document.

**Parameters:**
- `file` (file, required): PDF or DOCX file
- `slide_count` (int, form data, default: 6): Total number of slides
- `include_visuals` (bool, form data, default: false): Whether to include visuals
- `store` (bool, form data, default: true): Whether to store the presentation for later editing

**Response (if store=true):**
```json
{
  "presentation_id": "uuid-string",
  "slide_count": 6,
  "message": "Presentation generated successfully"
}
```

**Response (if store=false):**
Returns the PPTX file directly.

---

### List Presentations

#### `GET /presentations`
Get a list of all stored presentations.

**Response:**
```json
{
  "presentations": [
    {
      "id": "uuid-string",
      "metadata": {
        "created_at": "2024-01-01T12:00:00",
        "updated_at": "2024-01-01T12:00:00",
        "original_filename": "document.docx",
        "slide_count": 6
      },
      "slide_count": 6
    }
  ],
  "count": 1
}
```

---

### Get Presentation

#### `GET /presentations/{presentation_id}`
Get a specific presentation by ID.

**Response:**
```json
{
  "id": "uuid-string",
  "slides": [
    {
      "type": "title",
      "title": "Presentation Title"
    },
    {
      "type": "intro",
      "aim": "Purpose of presentation",
      "summary": "Brief summary"
    },
    {
      "type": "main",
      "title": "Main Topic",
      "point1": "Point 1",
      "point2": "Point 2",
      "point3": "Point 3",
      "point4": "Point 4",
      "visual": {
        "type": "image",
        "description": "Image description",
        "image_path": "path/to/image.png"
      }
    },
    {
      "type": "recommendation",
      "recommendation1": "Recommendation 1",
      "recommendation2": "Recommendation 2",
      "recommendation3": "Recommendation 3",
      "recommendation4": "Recommendation 4",
      "recommendation5": "Recommendation 5"
    }
  ],
  "metadata": {
    "created_at": "2024-01-01T12:00:00",
    "updated_at": "2024-01-01T12:00:00"
  }
}
```

---

### Update Presentation

#### `PUT /presentations/{presentation_id}`
Update all slides in a presentation.

**Request Body:**
```json
{
  "slides": [
    {
      "type": "title",
      "title": "Updated Title"
    },
    // ... other slides
  ]
}
```

**Response:**
```json
{
  "message": "Presentation updated successfully",
  "presentation": { /* updated presentation data */ }
}
```

---

### Update Single Slide

#### `POST /presentations/{presentation_id}/slides/{slide_index}`
Update a single slide in the presentation.

**Request Body:**
```json
{
  "type": "main",
  "title": "Updated Slide Title",
  "point1": "Updated point 1",
  "point2": "Updated point 2",
  "point3": "Updated point 3",
  "point4": "Updated point 4",
  "visual": {
    "type": "image",
    "description": "Image description"
  }
}
```

**Response:**
```json
{
  "message": "Slide updated successfully",
  "slide": { /* updated slide data */ },
  "slide_index": 2
}
```

---

### Get Single Slide

#### `GET /presentations/{presentation_id}/slides/{slide_index}`
Get a single slide from the presentation.

**Response:**
```json
{
  "slide": {
    "type": "main",
    "title": "Slide Title",
    "point1": "Point 1",
    // ... other fields
  },
  "slide_index": 2,
  "total_slides": 6
}
```

---

### Reorder Slides

#### `POST /presentations/{presentation_id}/reorder`
Reorder slides in a presentation (drag-and-drop functionality).

**Request Body:**
```json
{
  "slide_indices": [2, 0, 1, 3, 4, 5]
}
```

**Response:**
```json
{
  "message": "Slides reordered successfully",
  "presentation": { /* updated presentation */ }
}
```

---

### Delete Presentation

#### `DELETE /presentations/{presentation_id}`
Delete a presentation.

**Response:**
```json
{
  "message": "Presentation deleted successfully"
}
```

---

### Export as PowerPoint

#### `POST /presentations/{presentation_id}/export/pptx`
Export presentation as PowerPoint file.

**Response:**
Returns PPTX file download.

---

### Export as PDF

#### `POST /presentations/{presentation_id}/export/pdf`
Export presentation as PDF file.

**Response:**
Returns PDF file download.

---

### Generate Image for Slide

#### `POST /presentations/{presentation_id}/slides/{slide_index}/image`
Generate an AI image for a specific slide.

**Request Body:**
```json
{
  "description": "Optional custom description for image generation",
  "slide_title": "Optional slide title"
}
```

**Response:**
```json
{
  "message": "Image generated successfully",
  "image_path": "slide_image_uuid_2.png",
  "slide_index": 2
}
```

---

### Generate Images for All Slides

#### `POST /presentations/{presentation_id}/generate-all-images`
Generate images for all slides that have image visuals.

**Response:**
```json
{
  "message": "Generated 3 images",
  "generated_images": [
    {
      "slide_index": 2,
      "image_path": "slide_image_uuid_2.png",
      "description": "Image description"
    }
  ],
  "errors": []
}
```

---

### Get Templates

#### `GET /templates`
Get available presentation templates.

**Response:**
```json
{
  "templates": [
    {
      "id": "default",
      "name": "Default Template",
      "description": "Standard presentation template",
      "file": "format_new.pptx",
      "available": true
    }
  ]
}
```

---

## Slide Types

### Title Slide (`type: "title"`)
- `title` (string): Presentation title

### Introduction Slide (`type: "intro"`)
- `aim` (string): Purpose of the presentation
- `summary` (string): Brief summary (3-4 sentences)

### Main Slide (`type: "main"`)
- `title` (string): Slide title
- `point1`, `point2`, `point3`, `point4` (string): Main content points
- `visual` (object): Visual element
  - `type`: "none" | "image" | "bar" | "pie" | "line"
  - `title` (string): Visual title
  - `description` (string): For image type
  - `image_path` (string): Path to generated image (for image type)
  - `x`, `y` (array): Data for bar/line charts
  - `labels`, `sizes` (array): Data for pie charts
  - `xlabel`, `ylabel` (string): Axis labels for charts

### Recommendation Slide (`type: "recommendation"`)
- `recommendation1` through `recommendation5` (string): Recommendations

---

## Usage Examples

### 1. Generate a Presentation

```bash
curl -X POST "http://localhost:8000/generate" \
  -F "file=@document.docx" \
  -F "slide_count=8" \
  -F "include_visuals=true" \
  -F "store=true"
```

### 2. Get Presentation Data

```bash
curl "http://localhost:8000/presentations/{presentation_id}"
```

### 3. Update a Slide

```bash
curl -X POST "http://localhost:8000/presentations/{presentation_id}/slides/2" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "main",
    "title": "Updated Title",
    "point1": "New point 1",
    "point2": "New point 2",
    "point3": "New point 3",
    "point4": "New point 4",
    "visual": {"type": "none"}
  }'
```

### 4. Generate Images for All Slides

```bash
curl -X POST "http://localhost:8000/presentations/{presentation_id}/generate-all-images"
```

### 5. Export as PDF

```bash
curl -X POST "http://localhost:8000/presentations/{presentation_id}/export/pdf" \
  --output presentation.pdf
```

---

## Error Responses

All endpoints may return the following error responses:

- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Example error response:
```json
{
  "detail": "Error message here"
}
```

---

## Environment Variables

Required environment variables:
- `GOOGLE_API_KEY`: Google Gemini API key for AI generation
- `HF_API_KEY`: Hugging Face API key for image generation

---

## Notes

- Presentations are stored in JSON format in the `presentations_storage/` directory
- Generated images are saved in the project root directory
- The default template file `format_new.pptx` must be present in the project root
- All slide content is in Azerbaijani language by default
- Images are automatically translated to English for generation, then descriptions are stored in Azerbaijani

