from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.responses import JSONResponse, StreamingResponse
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
import asyncio
from typing import Dict

app = FastAPI()

# Temporary in-memory pairing store
image_store: Dict[str, Dict[int, str]] = {}

class PageInput(BaseModel):
    file_name: str  # e.g. "CornerRecord"
    page_index: int  # 1 or 2
    page_base64: str  # base64-encoded JPEG content

# Helper: decode base64 image
def base64_to_image(b64_str: str) -> Image.Image:
    image_data = base64.b64decode(b64_str)
    return Image.open(BytesIO(image_data)).convert("RGB")

# Helper: encode image as PDF bytes
def images_to_pdf_bytes(images: list[Image.Image]) -> BytesIO:
    pdf_buffer = BytesIO()
    images[0].save(pdf_buffer, format="PDF", save_all=True, append_images=images[1:])
    pdf_buffer.seek(0)
    return pdf_buffer

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

@app.post("/visualreview")
async def visual_review(data: PageInput, request: Request):
    # Store the incoming image page
    file_key = data.file_name
    page = data.page_index

    if file_key not in image_store:
        image_store[file_key] = {}

    image_store[file_key][page] = data.page_base64

    # Wait until both pages are received
    if 1 not in image_store[file_key] or 2 not in image_store[file_key]:
        return JSONResponse(content={"status": "waiting", "message": f"Received page {page}, waiting for other."})

    # Proceed with processing once both pages exist
    await asyncio.sleep(2)  # short safety delay

    # Decode both images
    img1 = base64_to_image(image_store[file_key][1])
    img2 = base64_to_image(image_store[file_key][2])

    # Placeholder: stamp text on images
    reviewed_img1 = stamp_image(img1, "Reviewed, ready for rules")
    reviewed_img2 = stamp_image(img2, "Reviewed, ready for rules")
    reviewed_images = [reviewed_img1, reviewed_img2]

    # Convert reviewed images to a single PDF
    pdf_bytes = images_to_pdf_bytes(reviewed_images)
    pdf_base64 = base64.b64encode(pdf_bytes.read()).decode("utf-8")

    # Cleanup
    del image_store[file_key]

    # Return base64-encoded PDF
    return JSONResponse(content={
        "file_name": f"{file_key}.pdf",
        "final_pdf_base64": pdf_base64
    })
