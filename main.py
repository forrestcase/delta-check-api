from fastapi import FastAPI, Response
from pydantic import BaseModel
import requests
import asyncio

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

def is_cover_page(text: str) -> bool:
    required_phrases = [
        "CORNER RECORD",
        "Brief  Legal Description",
        "County of",
        "City of",
        "California"
    ]
    return all(phrase in text for phrase in required_phrases)

@app.post("/deltacheck")
async def run_delta_check(data: ImagePair):
    await asyncio.sleep(5)  # Initial delay

    try:
        text1 = extract_text(data.image1)
        text2 = extract_text(data.image2)
    except Exception as e:
        return Response(content=f"OCR failed: {str(e)}", media_type="text/plain")

    # Determine if which image is the Cover
    line1 = "Line 1 = Cover" if is_cover_page(text1) else "Line 1 = Drawing"
    line2 = "Line 2 = Cover" if is_cover_page(text2) else "Line 2 = Drawing"

    # Fill lines 3 through 120 with placeholders
    remaining_lines = [f"Line {i}" for i in range(3, 121)]

    # Combine all lines
    all_lines = [line1, line2] + remaining_lines

    return Response(content="\n".join(all_lines), media_type="text/plain")
