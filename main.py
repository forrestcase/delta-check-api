from fastapi import FastAPI, Response
from pydantic import BaseModel
import requests

app = FastAPI()  # ✅ This line must be before any @app decorators

class ImagePair(BaseModel):
    image1: str
    image2: str

OCR_API_KEY = "K88435573088957"

def extract_text(base64_str: str) -> str:
    url = "https://api.ocr.space/parse/image"
    payload = {
        "base64Image": f"data:image/jpeg;base64,{base64_str}",
        "language": "eng",
        "isOverlayRequired": False,
        "OCREngine": 2
    }
    headers = {
        "apikey": OCR_API_KEY
    }

    response = requests.post(url, data=payload, headers=headers)
    result = response.json()

    try:
        return result["ParsedResults"][0]["ParsedText"]
    except (KeyError, IndexError):
        return "[OCR ERROR: No text extracted]"

@app.post("/deltacheck")
async def run_delta_check(data: ImagePair):
    try:
        text1 = extract_text(data.image1)
        text2 = extract_text(data.image2)
    except Exception as e:
        return Response(content=f"OCR failed: {str(e)}", media_type="text/plain")

    lines = [""] * 114

    cover_phrases = [
        "CORNER RECORD",
        "Brief  Legal Description",
        "County of",
        "City of",
        "California"
    ]

    score1 = sum(phrase in text1 for phrase in cover_phrases)
    score2 = sum(phrase in text2 for phrase in cover_phrases)

    if score1 >= 3 and score2 < 3:
        cover_text, drawing_text = text1, text2
        is_cover_first = True
    elif score2 >= 3 and score1 < 3:
        cover_text, drawing_text = text2, text1
        is_cover_first = False
    else:
        cover_text, drawing_text = text1, text2
        is_cover_first = True  # default fallback

    # Line 0: blank
    lines[0] = ""

    # Line 1: Try to extract Brief Legal Description
    bld_line = ""
    for line in cover_text.splitlines():
        if "Brief" in line and "Description" in line:
            bld_line = line.strip()
            break
    if not bld_line:
        caps_lines = [line.strip() for line in cover_text.splitlines() if line.isupper()]
        bld_line = max(caps_lines, key=len, default="[Brief Legal Description Not Found]")
    lines[1] = bld_line

    # Line 2: COVER or DRAWING
    lines[2] = "COVER" if is_cover_first else "DRAWING"

    # Lines 3–113: Just labeled placeholders for now
    for i in range(3, 114):
        lines[i] = f"Line {i}:"

    return Response(content="\n".join(lines), media_type="text/plain")
