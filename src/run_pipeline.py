import os
import json

def run_pipeline(user_input, env):
    from analyzer import generate_carousel_content
    from pollinationsAi import generate_and_download_image
    from typography import create_graphic

    # ✅ DEBUG: Print cwd and existing files BEFORE pipeline
    print(f"[DEBUG] Working directory: {os.getcwd()}")
    print(f"[DEBUG] Files before pipeline: {os.listdir('.')}")

    # 1. Analyze and get structure
    print("--- Step 1: Analyzing Content with Gemini ---")
    raw_data = generate_carousel_content(user_input, env)
    print(f"Content Plan generated successfully.")

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
            raise e
    else:
        data = raw_data

    final_slides = []

    for i in range(1, 5):
        print(f"\n--- Processing Slide {i} ---")
        slide_key = f"slide{i}"

        prompt = data[slide_key]["visual_prompt"]
        bg_image = generate_and_download_image(prompt, i, env)

        # ✅ DEBUG: Confirm bg_image was actually saved
        print(f"[DEBUG] bg_image path returned: {bg_image}")
        print(f"[DEBUG] bg_image exists on disk: {os.path.exists(bg_image)}")

        headline = data[slide_key]["headline"]
        body = data[slide_key]["body"]

        final_path = create_graphic(bg_image, headline, body, i)

        # ✅ DEBUG: Confirm final_path was actually saved
        print(f"[DEBUG] final_path returned: {final_path}")
        print(f"[DEBUG] final_path exists on disk: {os.path.exists(final_path)}")

        final_slides.append(final_path)

    # ✅ DEBUG: List ALL files after pipeline finishes
    print(f"\n[DEBUG] All files after pipeline: {os.listdir('.')}")
    print(f"[DEBUG] Working directory: {os.getcwd()}")

    print("\n--- Pipeline Finished Locally! ---")
    print(f"Caption: \n{data['caption']}")
    print(f"Final images ready for upload: {final_slides}")
    
    # ✅ Return final_slides so pipelineapi.py can use the exact paths
    return final_slides