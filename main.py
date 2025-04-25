from fastapi import FastAPI
from pydantic import BaseModel
import base64
import io
from PIL import Image
import pytesseract

app = FastAPI()

class ImagePair(BaseModel):
    image1: str
    image2: str

def decode_image(base64_str):
    header_removed = base64_str.split(",")[-1]
    image_data = base64.b64decode(header_removed)
    return Image.open(io.BytesIO(image_data))

def extract_text(image: Image.Image) -> str:
    return pytesseract.image_to_string(image)

@app.post("/deltacheck")
async def run_delta_check(data: ImagePair):
    try:
        img1 = decode_image(data.image1)
        img2 = decode_image(data.image2)
    except Exception as e:
        return {"error": f"Image decode failed: {str(e)}"}

    text1 = extract_text(img1)
    text2 = extract_text(img2)

    # Dummy rule output for testing
    result = "Rule 1: Pass\nRule 2: Fail: Missing 'City of'\nRule 3: Pass\n\n--- OCR Text Preview ---\n"
    result += (text1 + "\n\n" + text2)[:1000]

    return { "result": result }
