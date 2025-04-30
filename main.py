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

    # Determine if each image is Cover or Drawing
    line1 = "Line 1 = Cover" if is_cover_page(text1) else "Line 1 = Drawing"
    line2 = "Line 2 = Cover" if is_cover_page(text2) else "Line 2 = Drawing"

    # First 5 words from each OCR
    words1 = text1.split()
    words2 = text2.split()
    first_5_img1 = " ".join(words1[:5]) if words1 else "[No OCR output]"
    first_5_img2 = " ".join(words2[:5]) if words2 else "[No OCR output]"

    line3 = f"Line 3 = {first_5_img1}"
    line4 = f"Line 4 = {first_5_img2}"

    # Fill remaining lines
    remaining_lines = [f"Line {i}" for i in range(5, 121)]

    # Combine all
    all_lines = [line1, line2, line3, line4] + remaining_lines

    return Response(content="\n".join(all_lines), media_type="text/plain")
