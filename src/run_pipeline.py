import os
import json


def run_pipeline(user_input):
    from analyzer import generate_carousel_content
    from pollinationsAi import generate_and_download_image
    from typography import create_graphic

    print(f"[DEBUG] Working directory: {os.getcwd()}")
    print(f"[DEBUG] Files before pipeline: {os.listdir('.')}")

    print("--- Step 1: Analyzing Content with Gemini ---")
    raw_data = generate_carousel_content(user_input)
    print("Content Plan generated successfully.")

    if isinstance(raw_data, str):
        try:
            cleaned_data = raw_data.strip()
            if cleaned_data.startswith("```json"):
                cleaned_data = cleaned_data.split("```json")[1].split("```")[0].strip()
            elif cleaned_data.startswith("```"):
                cleaned_data = cleaned_data.split("```")[1].split("```")[0].strip()
            data = json.loads(cleaned_data)
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            raise
    else:
        data = raw_data

    final_slides = []

    for i in range(1, 5):
        print(f"\n--- Processing Slide {i} ---")
        slide_key = f"slide{i}"

        prompt = data[slide_key]["visual_prompt"]
        bg_image = generate_and_download_image(prompt, i)

        headline = data[slide_key]["headline"]
        body = data[slide_key]["body"]

        final_path = create_graphic(bg_image, headline, body, i)
        final_slides.append(final_path)

    print("\n--- Pipeline Finished! ---")
    print(f"Caption:\n{data.get('caption', '')}")
    print(f"Final images ready: {final_slides}")
    return final_slides
