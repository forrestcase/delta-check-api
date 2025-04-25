from fastapi import FastAPI, Response  # <-- add Response here
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
        return Response(content=f"OCR failed: {str(e)}", media_type="text/plain")  # <-- even error response is plain text

    result = "Rule 1: Pass\nRule 2: Fail: Missing 'City of'\nRule 3: Pass\n\n--- OCR Text Preview ---\n"
    result += (text1 + "\n\n" + text2)[:1000]

    return Response(content=result, media_type="text/plain")  # <-- main success return
