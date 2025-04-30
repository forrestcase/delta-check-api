from fastapi import FastAPI, Response
from pydantic import BaseModel
import requests

app = FastAPI()

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
        text1 = extract_text(data.image1)  # assumed drawing
        text2 = extract_text(data.image2)  # assumed cover
    except Exception as e:
        return Response(content=f"OCR failed: {str(e)}", media_type="text/plain")

    lines = [""] * 114
    lines[0] = ""

    # --- LINE 1 and 58: Brief Legal Description (image2 only) ---
    bld_line = ""
    for line in text2.splitlines():
        if "Brief" in line and "Description" in line:
            bld_line = line.strip()
            break
    if not bld_line:
        caps_lines = [line.strip() for line in text2.splitlines() if line.isupper()]
        bld_line = max(caps_lines, key=len, default="[Brief Legal Description Not Found]")
    lines[1] = bld_line
    lines[58] = bld_line

    # --- LINE 59: COVER or DRAWING based ONLY on image2 ---
    cover_phrases = [
        "CORNER RECORD",
        "Brief  Legal Description",
        "County of",
        "City of",
        "California"
    ]
    score_image2 = sum(phrase in text2 for phrase in cover_phrases)
    lines[59] = "COVER" if score_image2 >= 3 else "DRAWING"

    # --- Fill the rest with placeholders ---
    for i in range(2, 58):
        if i != 57:  # You said line 57 is reserved for font work
            lines[i] = f"Line {i}:"
    for i in range(60, 114):
        lines[i] = f"Line {i}:"

    return Response(content="\n".join(lines), media_type="text/plain")

