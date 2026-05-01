import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()


# CONFIGURATION
CIVITAI_API_KEY = os.getenv("CIVITAI_API_KEY")
# Standard SDXL Base model (for good compatibility)
MODEL_VERSION_ID = 101053 
BASE_URL = "https://civitai.com/api/v1"

def generate_and_download_image(prompt, slide_number):
    headers = {
        "Authorization": f"Bearer {CIVITAI_API_KEY}",
        "Content-Type": "json"
    }

    # 1. Prepare the Generation Request
    payload = {
        "modelVersionId": MODEL_VERSION_ID,
        "params": {
            "prompt": prompt,
            "negativePrompt": "blurry, low quality, distorted, text, signature",
            "scheduler": "EulerA",
            "steps": 30,
            "cfgScale": 7,
            "width": 1024, # SDXL likes higher resolutions
            "height": 1024,
            "clipSkip": 2
        }
    }

    # 2. Submit the Job
    print(f"Submitting Slide {slide_number} generation request...")
    response = requests.post(f"{BASE_URL}/image/generate", json=payload, headers=headers)
    
    if response.status_code != 200:
        raise RuntimeError(f"Error submitting request: {response.text}")

    job_data = response.json()
    job_id = job_data['jobId']
    print(f"Job submitted successfully. Job ID: {job_id}")

    # 3. Poll for Completion (Wait until the servers are done)
    status_url = f"{BASE_URL}/image/jobs/{job_id}"
    print(f"Waiting for generation to finish...")
    
    while True:
        status_response = requests.get(status_url, headers=headers)
        if status_response.status_code != 200:
            print("Error checking job status. Retrying...")
            continue
            
        job_status_data = status_response.json()
        status = job_status_data['status']

        if status == 'Completed':
            print("Image generated successfully!")
            image_url = job_status_data['jobs'][0]['result']['imageUrl']
            break
        elif status == 'Failed':
            raise RuntimeError(f"Job failed: {job_status_data}")
        elif status in ['Pending', 'Processing']:
            # Still working, wait a few seconds before checking again
            print("Still processing... (waiting 5 seconds)")
            time.sleep(5)
        else:
            print(f"Unknown status: {status}")

    # 4. Download the Final Image
    print(f"Downloading final image for Slide {slide_number}...")
    img_data = requests.get(image_url).content
    filename = f"slide_{slide_number}.png"
    with open(filename, 'wb') as handler:
        handler.write(img_data)
    print(f"Saved as {filename}")
    return filename

# --- Test Module ---
if __name__ == "__main__":
    # Ensure you set your API key above before running this!
    test_prompt = "A hyper-realistic close-up of a digital computer chip on a motherboard, glowing blue LED accents, shallow depth of field, high quality photography"
    generate_and_download_image(test_prompt, 1)