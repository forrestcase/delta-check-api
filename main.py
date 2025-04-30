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

    is_image1_cover = score1 >= 3
    is_image2_cover = score2 >= 3

    # Identify which image is the Cover to extract BLD from
    cover_text = text1 if is_image1_cover else text2
    cover_lines = cover_text.splitlines()

    bld_line = ""
    for line in cover_lines:
        if "Brief" in line and "Description" in line:
            bld_line = line.strip()
            break
    if not bld_line:
        caps_lines = [line.strip() for line in cover_lines if line.isupper()]
        bld_line = max(caps_lines, key=len, default="[Brief Legal Description Not Found]")

    # Fill the required lines
    lines[0] = ""
    lines[1] = bld_line
    lines[2] = "COVER" if is_image1_cover else "DRAWING"
    lines[57] = bld_line
    lines[58] = "COVER" if is_image2_cover else "DRAWING"

    # Fill placeholders for the rest
    for i in range(3, 57):
        lines[i] = f"Line {i}:"
    for i in range(59, 114):
        lines[i] = f"Line {i}:"

    return Response(content="\n".join(lines), media_type="text/plain")
