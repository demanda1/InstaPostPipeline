from PIL import Image, ImageDraw, ImageFont
import os

def wrap_text(text, font, max_width):
    """Split text into lines that fit within max_width."""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        # Use getbbox to calculate width: (left, top, right, bottom)
        bbox = font.getbbox(test_line)
        w = bbox[2] - bbox[0]
        
        if w <= max_width:
            current_line.append(word)
        else:
            lines.append(' '.join(current_line))
            current_line = [word]
    
    lines.append(' '.join(current_line))
    return lines

def create_graphic(background_path, headline_text, body_text, slide_number):
    print(f"Adding wrapped typography to {background_path}...")
    img = Image.open(background_path).convert("RGBA")
    width, height = img.size
    draw = ImageDraw.Draw(img)

    # 1. Setup Fonts
    font_path = "/System/Library/Fonts/Helvetica.ttc"
    headline_font = ImageFont.truetype(font_path, 60, index=1)
    body_font = ImageFont.truetype(font_path, 35, index=0)

    # 2. Settings
    margin = 60
    max_text_width = width - (margin * 2)
    
    # 3. Wrap the text
    headline_lines = wrap_text(headline_text.upper(), headline_font, max_text_width)
    body_lines = wrap_text(body_text, body_font, max_text_width)

    # 4. Calculate total height for the background box
    line_height_h = headline_font.getbbox("Ay")[3] - headline_font.getbbox("Ay")[1] + 10
    line_height_b = body_font.getbbox("Ay")[3] - body_font.getbbox("Ay")[1] + 8
    
    total_text_height = (len(headline_lines) * line_height_h) + (len(body_lines) * line_height_b) + 60
    
    # 5. Draw background overlay
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    box_y_start = height - total_text_height - margin
    draw_ov.rectangle([0, box_y_start, width, height], fill=(0, 0, 0, 170))
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # 6. Draw Text
    current_y = box_y_start + 30
    
    for line in headline_lines:
        draw.text((margin, current_y), line, font=headline_font, fill=(255, 255, 255))
        current_y += line_height_h
    
    current_y += 10 # Extra gap between headline and body
    
    for line in body_lines:
        draw.text((margin, current_y), line, font=body_font, fill=(230, 230, 230))
        current_y += line_height_b

    # 7. Save
    final_img = img.convert("RGB")
    final_filename = f"final_slide_{slide_number}.jpg"
    final_img.save(final_filename)
    return final_filename

# --- Standalone Test ---
if __name__ == "__main__":
    # Test this standalone by providing an existing image (e.g., slide_1.png)
    if os.path.exists("slide_1.png"):
        create_graphic(
            "slide_1.png", 
            "The Power of M1", 
            "A dynamic, abstract visualization of data flow and speed. A complex, photorealistic image (e.g., a detailed futuristic city or an intricate creature) is rapidly forming on a transparent digital canvas. Streaks of light, geometric patterns, and energetic particles burst forth from a subtle, glowing M1 chip icon in the bottom corner, illustrating incredible processing speed and efficiency as the image instantly materializes with high fidelity. Digital art style, vibrant colors, motion blur..",
            1
        )
        print("Final professional graphic created. Check 'final_slide_1.jpg'.")
    else:
        print("Please ensure 'slide_1.png' exists in this folder for the test.")