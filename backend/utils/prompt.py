
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from huggingface_hub import InferenceClient
import os
import re
import json
import textwrap

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use system environment variables

import sys
# Force UTF-8 encoding for stdout/stderr on Windows to avoid UnicodeEncodeError
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # For older Python versions that don't support reconfigure
        pass


def build_prompt(text, slide_count=6, include_visuals=False):
    remaining = slide_count - 3

    if include_visuals:
        main = remaining // 2
        extra = remaining % 2  # will be 1 if odd
        if extra == 1:
            main += 1
        else:
            slide_count = main + 3
        note = (
            "• Qeyd: Slayd sayı tam bölünmədiyi üçün sonuncu Əsas slayd `visual.type = 'none'` olaraq təyin edilməlidir."
            if extra == 1 else ""
        )
    else:
        main = remaining
        note = ""
    return f"""
Sənə bir sənədin mətni təqdim olunur. Bu mətni təhlil et və təqdimat üçün aşağıdakı struktura uyğun slayd formatında hazırla:

TƏQDİMATIN STRUKTURU:
1. Başlıq – Təqdimatın adı 
2. Giriş – Məqsəd və təqdim olunacaq mövzu üzrə qısa xülasə
3. Əsas Slaydlar – Mətndəki əsas mövzulardan hər biri üçün ayrıca slayd:
   • Hər biri unikal başlığa sahib olmalıdır  
   • Hər slaydda **4 əsas bənd** olmalıdır  
   • Slayd sayı: İstifadəçi {slide_count} slayd istəmişdir, bu saydan **1 başlıq**, **1 giriş**, **1 tövsiyə** slayd çıxıldıqdan sonra qalan **{main}** slayd əsas mövzular üçün istifadə olunmalıdır. 
4. Tövsiyə – Gələcək inkişaf və təkmilləşdirmə üçün 4–5 bəndlik təkliflər.

QAYDALAR:
- İstifadəçi {slide_count} slayd istəmişdir. Mətni analiz et və bu sayda slayda uyğun şəkildə ayır.
- Hər slayd üçün JSON obyektində aşağıdakı sahələri yaz:
  - type: "title" | "intro" | "main" | "recommendation"
  - Başlıq üçün (type = "title"):
    • title (təqdimatın adı)
  - Giriş üçün (type = "intro"):
    • aim (təqdimatın məqsədi)
    • summary (layihənin qısa xülasəsi, 3-4 cümlə)
  - Əsas slaydlar üçün (type = "main"):
    • title (slaydın başlığı)
    • point1, point2, point3, point4 (hər biri əsas məzmun bəndləri)
    • visual (vizual təklif üçün JSON obyekti, aşağıdakı formatda)
  - Tövsiyə slaydı üçün (type = "recommendation"):
    • recommendation1, recommendation2, recommendation3, recommendation4, (optional) recommendation5
- Hər slayd üçün:
  • Mətni slayd sayına uyğun şəkildə bərabər böl.
  • Cümlə dəyərlərinin içində qaçırılmamış qoşa dırnaq işarələrindən istifadə etmə. Daxili dırnaq işarələri üçün tək dırnaqdan istifadə et.
  • Lazımsız təkrarlardan, çox uzun cümlələrdən qaç.
  • Slayd dili **rəsmi və aydın olmalıdır**.
  • Əgər statistik və ya əsas nəticələr varsa, Əsas Göstəricilər slaydına daxil et.
  • Slaydların məzmunu yalnız sənədə əsaslanmalıdır, əlavə məlumat əlavə etmə.
  {note}

- Vizual təklif JSON formatı (mümkün olduqca fərqli növ vizuallar əlavə et, type image daxil olmaqla.):
    ```json
    {{
        "type": "none" | "image" | "bar" | "pie" | "line",
        "title": "Vizualın başlığı",
        "description": "Əgər type 'image'dirsə, burada şəkilin ətraflı təsviri verilir. Digər hallarda boş saxlanılır.",
        "xlabel": "X oxunun etiketi (əgər tətbiq olunursa)",
        "ylabel": "Y oxunun etiketi (əgər tətbiq olunursa)",
        "x": ["X oxundakı dəyərlər (əgər varsa)"],
        "y": ["Y oxundakı dəyərlər (əgər varsa)"],
        "labels": ["Dilim adları (əgər 'pie' tipi tətbiq olunursa)"],
        "sizes": ["Dilim ölçüləri (əgər 'pie' tipi tətbiq olunursa)"]
    }}
    ```

    - `type` sahəsi yalnız aşağıdakı dəyərlərdən biri ola bilər: "none", "image", "bar", "pie", "line"
    - `type` = "image" olduqda, `description` sahəsi vacibdir və şəkilin məzmununu izah etməlidir.
    - `type` = "bar" və ya "line" olduqda x, y, xlabel, ylabel sahələri dolu olmalıdır.
    -  Əgər uyğun vizual yoxdursa, `type` dəyəri `"none"` olmalıdır.
    - `type` = "pie" olduqda labels və sizes sahələri dolu olmalı, `x`, `y`, `xlabel`, `ylabel` isə boş buraxılmalıdır.
    - `type` = "none" olduqda digər sahələr boş buraxılmalıdır.

TƏHLİL EDİLƏCƏK SƏNƏDİN MƏTNI:
\"\"\"
{text}
\"\"\"

CAVABI BU FORMATA JSON ARRAY KİMİ QAYTAR:

```json
[
  {{
    "type": "title",
    "title": "Təqdimatın adı",
  }},
  {{
    "type": "intro",
    "aim": "Təqdimatın məqsədi",
    "summary": "Layihənin qısa xülasəsi"
  }},
  {{
    "type": "main",
    "title": "Əsas mövzunun başlığı",
    "point1": "...",
    "point2": "...",
    "point3": "...",
    "point4": "...",
    "visual": {{
      "type": "bar",
      "title": "",
      "description": "",
      "xlabel": "",
      "ylabel": "",
      "x": [],
      "y": [],
      "labels": [],
      "sizes": []
    }}
  }},
  ...
  {{
    "type": "recommendation",
    "recommendation1": "...",
    "recommendation2": "...",
    "recommendation3": "...",
    "recommendation4": "...",
    "recommendation5": "..."
  }}
]
```
"""


def build_offline_presentation(text, slide_count):
    sentences = [s.strip() for s in re.split(r'[\.\n]+', text) if s.strip()]
    title = (sentences[0] if sentences else "Təqdimat")[:60]
    remaining = max(slide_count - 3, 1)

    mains = []
    idx = 0
    for i in range(remaining):
        points = []
        for _ in range(4):
            if idx < len(sentences):
                points.append(textwrap.shorten(sentences[idx], width=120, placeholder="…"))
                idx += 1
            else:
                points.append("")
        mains.append({
            "type": "main",
            "title": f"Mövzu {i+1}",
            "point1": points[0],
            "point2": points[1],
            "point3": points[2],
            "point4": points[3],
            "visual": {"type": "none", "title": "", "description": "", "xlabel": "", "ylabel": "", "x": [], "y": [], "labels": [], "sizes": []}
        })

    slides = [
        {"type": "title", "title": title},
        {"type": "intro", "aim": "Sənədin əsas ideyalarını təqdim etmək", "summary": textwrap.shorten(" ".join(sentences[:5]), width=300, placeholder="…")},
        *mains,
        {"type": "recommendation", "recommendation1": "Məzmunu daha da dəqiqləşdirin", "recommendation2": "Əlavə sübutlar toplayın", "recommendation3": "Riskləri qiymətləndirin", "recommendation4": "Növbəti mərhələləri planlayın", "recommendation5": "Komanda ilə paylaşın"}
    ]
    return json.dumps(slides, ensure_ascii=False)


def get_presentation(text, slide_count=6, model_name='gemini-pro', include_visuals=False):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return build_offline_presentation(text, slide_count)

    genai.configure(api_key=api_key)
    
    # Try different model names with correct format
    # First, try to list available models to see what's actually available
    available_model_names = []
    try:
        print("Checking available models from API...")
        for model in genai.list_models():
            if 'generateContent' in model.supported_generation_methods:
                model_full_name = model.name  # This already includes 'models/' prefix
                model_short_name = model.name.replace('models/', '')
                if not any(x in model_short_name.lower() for x in ["exp", "preview", "beta", "gemma"]):
                    available_model_names.append(model_full_name)
                print(f"Found available model: {model_full_name}")
        
        if available_model_names:
            print(f"Using {len(available_model_names)} available model(s)")
    except Exception as e:
        print(f"Could not list models from API: {e}")
        print("Will try default model list...")
    
    # Try different model names with correct format
    # Prioritize models found from API, then try common ones
    model_names_to_try = []
    
    # First, add models we found from the API
    for av_model in available_model_names:
        if av_model not in model_names_to_try:
            model_names_to_try.append(av_model)
    
    # Then add the provided model name (if any)
    if model_name:
        provided_model = model_name if model_name.startswith('models/') else f'models/{model_name}'
        if provided_model not in model_names_to_try:
            model_names_to_try.append(provided_model)
    
    # Add common fallback models (only if we didn't find any from API)
    if not available_model_names:
        fallback_models = [
            'models/gemini-1.5-flash-8b',
            'models/gemini-1.5-flash',
            'models/gemini-1.5-pro',
            'models/gemini-pro',
            'gemini-1.5-flash-8b',
            'gemini-1.5-flash',
            'gemini-1.5-pro',
            'gemini-pro',
        ]
        for m in fallback_models:
            if m not in model_names_to_try:
                model_names_to_try.append(m)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_models = []
    for m in model_names_to_try:
        if m and m not in seen:
            seen.add(m)
            unique_models.append(m)
    model_names_to_try = unique_models
    
    if not model_names_to_try:
        raise ValueError("No models available. Please check your API key and ensure Generative AI API is enabled.")
    
    print(f"Will try these models in order: {model_names_to_try}")
    
    # Truncate text if it's too long (Gemini has token limits)
    # Rough estimate: 1 token ≈ 4 characters, so 1M tokens ≈ 4M characters
    # For safety, limit to ~500k characters (~125k tokens) to leave room for prompt
    MAX_TEXT_LENGTH = 500000
    
    original_text_length = len(text)
    if len(text) > MAX_TEXT_LENGTH:
        print(f"Warning: Text is too long ({original_text_length} chars). Truncating to {MAX_TEXT_LENGTH} chars.")
        truncated = text[:MAX_TEXT_LENGTH]
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')
        last_boundary = max(last_period, last_newline)
        if last_boundary > MAX_TEXT_LENGTH * 0.9:
            text = truncated[:last_boundary + 1]
        else:
            text = truncated
        print(f"Text truncated to {len(text)} characters.")
    
    prompt = build_prompt(text, slide_count, include_visuals)
    print(f"Prompt length: {len(prompt)} characters, Text length: {len(text)} characters")
    
    generation_config = GenerationConfig(
        temperature=0.3,
        max_output_tokens=4096,
    )

    # Try each model name until one works
    last_error = None
    for current_model_name in model_names_to_try:
        try:
            print(f"Trying model: {current_model_name}")
            try:
                model = genai.GenerativeModel(
                    model_name=current_model_name,
                    system_instruction="Sən təqdimat üzrə Azərbaycan dilində AI asistentsən. Sənəvərə cavabını YALNIZ JSON formatında qaytar. Heç bir əlavə mətn, izahat və ya formatlaşdırma olmadan."
                )
            except Exception as e:
                if "Developer instruction is not enabled" in str(e):
                    print(f"Model {current_model_name} does not support system_instruction; trying without...")
                    model = genai.GenerativeModel(model_name=current_model_name)
                else:
                    raise
            
            # Send the prompt to the Gemini model
            response = model.generate_content(
                contents=[
                    {"role": "user", "parts": [{"text": prompt}]}
                ],
                generation_config=generation_config
            )

            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                finish_reason = getattr(candidate, 'finish_reason', None)
                # Check for various forms of STOP (1, "STOP", FinishReason.STOP)
                is_stop = (
                    str(finish_reason) == 'STOP' or 
                    str(finish_reason) == 'FinishReason.STOP' or 
                    finish_reason == 1
                )
                
                if finish_reason and not is_stop:
                    print(f"Response blocked. Finish reason: {finish_reason}. Trying next model or fallback.")
                    last_error = ValueError(f"Response blocked. Finish reason: {finish_reason}")
                    continue
                
                if candidate.content and candidate.content.parts:
                    response_text = candidate.content.parts[0].text
                    if not response_text:
                        raise ValueError("Empty response received from API. The model did not generate any content.")
                    
                    print(f"Successfully used model: {current_model_name}")
                    print(f"Response received: {len(response_text)} characters")
                    print(f"Response preview: {response_text[:200]}...")
                    
                    return response_text
                else:
                    raise ValueError("Model did not return expected content structure. Response has no content parts.")
            else:
                raise ValueError("No candidates in response. The API may have encountered an error.")
        
        except Exception as e:
            error_str = str(e)
            if (
                "not found" in error_str.lower() or
                "not supported" in error_str.lower() or
                "404" in error_str or
                "quota" in error_str.lower() or
                "rate limit" in error_str.lower() or
                "429" in error_str or
                "Response blocked" in error_str
            ):
                print(f"Model {current_model_name} failed: {error_str}")
                last_error = e
                continue
            raise
    
    # If we tried all models and none worked, raise the last error
    if last_error:
        return build_offline_presentation(text, slide_count)


def generate_image_hf(prompt, output_path):
    hf_key = os.getenv("HF_API_KEY")
    if not hf_key:
        # Graceful no-op when no HF key is set; caller may insert fallback text
        return None
    client = InferenceClient(
        provider="hf-inference",
        api_key=hf_key

    )

    # This returns a PIL.Image object
    image = client.text_to_image(
        prompt,
        model="stabilityai/stable-diffusion-3-medium-diffusers",
    )

    # Save PIL image to file
    image.save(output_path)
    return output_path
