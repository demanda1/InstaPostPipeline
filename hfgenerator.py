from huggingface_hub import InferenceClient
import io
from PIL import Image
import time
import os
from dotenv import load_dotenv

load_dotenv()

hf_key = os.getenv("HUGGINGFFACE_TOKEN")

# CONFIG
# Using a highly stable model for the free API
MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
client = InferenceClient(token=hf_key)

def generate_and_download_image(prompt, slide_number):
    print(f"Requesting Slide {slide_number} via HF InferenceClient...")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # text_to_image handles the POST and endpoint routing for you
            image = client.text_to_image(
                prompt,
                model=MODEL_ID,
                width=1024,
                height=1024
            )
            
            filename = f"slide_{slide_number}.png"
            image.save(filename)
            print(f"Successfully saved {filename}")
            return filename

        except Exception as e:
            # If the model is loading (503), it usually raises an error we can catch
            if "503" in str(e) or "loading" in str(e).lower():
                print(f"Model is warming up... waiting 20s (Attempt {attempt+1}/{max_retries})")
                time.sleep(20)
                continue
            else:
                print(f"An unexpected error occurred: {e}")
                raise e

if __name__ == "__main__":
    test_prompt = "A high-tech digital circuit board, cinematic lighting, 8k resolution, professional"
    generate_and_download_image(test_prompt, 1)