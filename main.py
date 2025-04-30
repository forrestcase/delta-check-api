from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from PIL import Image, ImageDraw, ImageFont
from pdf2image import convert_from_bytes
from io import BytesIO
import base64
import asyncio

app = FastAPI()

class PDFInput(BaseModel):
    file_name: str  # e.g. "CornerRecord"
    pdf_base64: str  # base64-encoded PDF content

# Helper: overlay placeholder text
def stamp_image(img: Image.Image, text: str) -> Image.Image:
    draw = ImageDraw.Draw(img)
    width, height = img.size
    font_size = int(height * 0.03)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()
    text_width, text_height = draw.textsize(text, font=font)
    position = ((width - text_width) // 2, (height - text_height) // 2)
    draw.text(position, text, fill="red", font=font)
    return img

# Helper: encode image to base64 JPEG string
def image_to_base64_jpg(img: Image.Image) -> str:
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

@app.post("/visualreview")
async def visual_review(data: PDFInput, request: Request):
    await asyncio.sleep(2)  # short safety delay

    # Decode PDF
    pdf_bytes = base64.b64decode(data.pdf_base64)

    # Convert PDF to images (one image per page)
    try:
        images = convert_from_bytes(pdf_bytes)
    except Exception as e:
        return JSONResponse(content={"error": f"PDF conversion failed: {str(e)}"}, status_code=400)

    # Stamp and convert the first page only
    stamped = stamp_image(images[0], "Reviewed, ready for rules")
    stamped_base64 = image_to_base64_jpg(stamped)

    return JSONResponse(content={
        "file_name": f"{data.file_name}.jpg",
        "jpg_base64": stamped_base64
    })
