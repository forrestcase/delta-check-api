@app.post("/deltacheck")
async def run_delta_check(data: ImagePair):
    try:
        text1 = extract_text(data.image1)
        text2 = extract_text(data.image2)
    except Exception as e:
        return Response(content=f"OCR failed: {str(e)}", media_type="text/plain")

    # Set up output
    lines = [""] * 114  # will populate lines[0] through lines[113]

    cover_phrases = [
        "CORNER RECORD",
        "Brief  Legal Description",
        "County of",
        "City of",
        "California"
    ]

    # Determine which image is cover based on OCR text
    score1 = sum(phrase in text1 for phrase in cover_phrases)
    score2 = sum(phrase in text2 for phrase in cover_phrases)

    if score1 >= 3 and score2 < 3:
        cover_text, drawing_text = text1, text2
    elif score2 >= 3 and score1 < 3:
        cover_text, drawing_text = text2, text1
    else:
        cover_text, drawing_text = text1, text2  # fallback if uncertain

    # Line 1: Try to find the Brief Legal Description
    bld_line = ""
    for line in cover_text.splitlines():
        if "Brief" in line and "Description" in line:
            bld_line = line.strip()
            break
    if not bld_line:
        # fallback: find longest ALL CAPS line
        caps_lines = [line.strip() for line in cover_text.splitlines() if line.isupper()]
        bld_line = max(caps_lines, key=len, default="[Brief Legal Description Not Found]")

    lines[0] = ""  # Line 0 = blank
    lines[1] = bld_line  # Line 1 = Brief Legal Description
    lines[2] = "COVER" if cover_text in [text1, text2] and score1 >= 3 or score2 >= 3 else "DRAWING"

    # Fill lines 3 through 113 with placeholders
    for i in range(3, 114):
        lines[i] = f"Line {i}:"

    return Response(content="\n".join(lines), media_type="text/plain")
