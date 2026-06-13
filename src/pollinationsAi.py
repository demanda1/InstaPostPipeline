import io
import os
import random
import time
import urllib.parse

import requests
from PIL import Image


def generate_and_download_image(prompt, slide_number):
    api_key = os.getenv("POLLINATION_KEY")
    if not api_key:
        raise ValueError("POLLINATION_KEY is missing!")

    print(f"--- Processing Slide {slide_number} ---")

    base_url = "https://gen.pollinations.ai/image"
    safe_prompt = urllib.parse.quote(prompt, safe="")
    unique_seed = random.randint(1, 9_999_999)

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

    max_retries = 3
    for attempt in range(max_retries):
        try:
            use_query_key = attempt > 0
            url = build_url(unique_seed, use_query_key=use_query_key)
            headers = {} if use_query_key else {"Authorization": f"Bearer {api_key}"}

            response = requests.get(url, headers=headers, timeout=120)

            if response.status_code == 401:
                raise Exception(f"Unauthorized (401): {response.text}")

            if response.status_code == 429:
                unique_seed = random.randint(1, 9_999_999)
                print(f"Rate limited. Retrying in 15s... ({attempt + 1}/{max_retries})")
                time.sleep(15)
                continue

            response.raise_for_status()
            image_bytes = response.content

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
