import io
import json
import base64
from PIL import Image
import os
import time
import js
from pyodide.ffi import run_sync

def generate_and_download_image(prompt, slide_number, env):
    print(f"Requesting Slide {slide_number} via Gemini Flash Image...")

    api_key = getattr(env, "GENAI_APIKEY", os.getenv("GENAI_APIKEY"))
    if not api_key:
        raise ValueError("GENAI_APIKEY is missing!")

    # Updated to the correct Free Tier image generation model
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent"

    # Simplified payload: no responseModalities needed for dedicated image models
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }

    js_options_str = json.dumps({
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        },
        "body": json.dumps(payload)
    })

    max_retries = 3
    for attempt in range(max_retries):
        try:
            options_object = js.JSON.parse(js_options_str)
            promise = js.fetch(url, options_object)
            response = run_sync(promise)

            if response.status == 429:
                print(f"Rate limit... waiting 30s (Attempt {attempt+1}/{max_retries})")
                time.sleep(30)
                continue

            if not response.ok:
                error_text = run_sync(response.text())
                raise Exception(f"Google API error {response.status}: {error_text}")

            response_text = run_sync(response.text())
            data = json.loads(response_text)

            # Your existing parsing logic works perfectly with the new model!
            parts = data["candidates"][0]["content"]["parts"]
            image_part = next(p for p in parts if "inlineData" in p)
            image_bytes = base64.b64decode(image_part["inlineData"]["data"])

            image = Image.open(io.BytesIO(image_bytes))
            filename = f"slide_{slide_number}.png"
            image.save(filename)
            print(f"Successfully saved: {filename}")
            return filename

        except Exception as e:
            print(f"Error on attempt {attempt+1}: {e}")
            if attempt == max_retries - 1:
                raise e
            time.sleep(5)