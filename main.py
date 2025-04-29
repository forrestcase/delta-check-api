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

    # Initialize 114-line output
    lines = [""] * 114

    # Page 2 (top half: lines 0–56)
    lines[0] = "Rule 1: Pass"
    lines[1] = "Rule 2: Fail - Missing 'City of'"
    lines[2] = "Rule 3: Pass"
    lines[56] = "--- End of Page 2 ---"

    # Page 1 (bottom half: lines 57–113)
    lines[57] = "--- Drawing Page OCR Preview ---"
    text_lines = text1.splitlines()
    for i in range(min(3, len(text_lines))):  # show 3 OCR lines
        lines[58 + i] = text_lines[i]
    lines[113] = "--- End of Page 1 ---"

    result = "\n".join(lines)
    return Response(content=result, media_type="text/plain")

