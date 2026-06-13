import io
import json
import urllib.parse
import random
import time
from PIL import Image
import js
import os
from pyodide.ffi import run_sync

def generate_and_download_image(prompt, slide_number, env):
    
    api_key = getattr(env, "POLLINATION_KEY", os.getenv("POLLINATION_KEY"))
    if not api_key:
        raise ValueError("POLLINATION_KEY is missing!")


    print(f"--- Processing Slide {slide_number} ---")

    base_url = "https://gen.pollinations.ai/image"
    safe_prompt = urllib.parse.quote(prompt, safe="")
    unique_seed = random.randint(1, 9999999)

    def build_url(seed, use_query_key=False):
        params = {
            "model": "flux",
            "width": 1024,
            "height": 1024,
            "seed": seed,
            "enhance": "false",
        }
        if use_query_key:
            params["key"] = api_key
        return f"{base_url}/{safe_prompt}?{urllib.parse.urlencode(params)}"

    def fetch_image(use_query_key=False):
        url = build_url(unique_seed, use_query_key=use_query_key)

        js_options = {"method": "GET"}
        if not use_query_key:
            js_options["headers"] = {"Authorization": f"Bearer {api_key}"}

        options_object = js.JSON.parse(json.dumps(js_options))
        return run_sync(js.fetch(url, options_object))

    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Try Bearer header first, then ?key= on retry
            response = fetch_image(use_query_key=(attempt > 0))

            if response.status == 401:
                error_text = run_sync(response.text())
                raise Exception(f"Unauthorized (401): {error_text}")

            if response.status == 429:
                unique_seed = random.randint(1, 9999999)
                print(f"Rate limited. Retrying in 15s... ({attempt + 1}/{max_retries})")
                time.sleep(15)
                continue

            if not response.ok:
                error_text = run_sync(response.text())
                raise Exception(f"API error {response.status}: {error_text}")

            array_buffer = run_sync(response.arrayBuffer())
            image_bytes = bytes(js.Uint8Array.new(array_buffer).to_py())

            if len(image_bytes) < 1000:
                raise ValueError(image_bytes.decode("utf-8", errors="ignore"))

            image = Image.open(io.BytesIO(image_bytes))
            filename = f"slide_{slide_number}.png"
            image.save(filename)
            print(f"Successfully saved: {filename}")
            return filename

        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(5)
