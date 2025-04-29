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
        lines[0] = "Page 1: Cover"
        lines[57] = "Page 2: Drawing"
    elif score2 >= 3 and score1 < 3:
        lines[0] = "Page 1: Drawing"
        lines[57] = "Page 2: Cover"
    elif score1 >= 3 and score2 >= 3:
        lines[0] = "Page 1: Cover (conflict - both look like Covers)"
        lines[57] = "Page 2: Cover (conflict - both look like Covers)"
    else:
        lines[0] = "Page 1: Drawing (uncertain)"
        lines[57] = "Page 2: Drawing (uncertain)"

    lines[56] = "--- End of Page 2 ---"
    lines[113] = "--- End of Page 1 ---"

    return Response(content="\n".join(lines), media_type="text/plain")
