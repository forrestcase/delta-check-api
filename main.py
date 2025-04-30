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
        text1 = extract_text(data.image1)
        text2 = extract_text(data.image2)
    except Exception as e:
        return Response(content=f"OCR failed: {str(e)}", media_type="text/plain")

    # Tokenize image1 text
    words1 = text1.split()
    first_20_img1 = " ".join(words1[:20])
    last_20_img1 = " ".join(words1[-20:]) if len(words1) >= 20 else " ".join(words1)

    # Tokenize image2 text
    words2 = text2.split()
    first_20_img2 = " ".join(words2[:20])
    last_20_img2 = " ".join(words2[-20:]) if len(words2) >= 20 else " ".join(words2)

    # Initialize all lines
    lines = [f"Line {i}:" for i in range(120)]

    # Populate OCR summaries
    lines[28] = first_20_img1
    lines[29] = last_20_img1
    lines[30] = first_20_img2
    lines[31] = last_20_img2

    return Response(content="\n".join(lines), media_type="text/plain")
