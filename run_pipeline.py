from analyzer import generate_carousel_content
from hfgenerator import generate_and_download_image
from typography import create_graphic
import os

def run_pipeline(user_input):
    # 1. Analyze and get structure (Updated for smart prompt)
    print("--- Step 1: Analyzing Content with Gemini ---")
    data = generate_carousel_content(user_input)
    print(f"Content Plan generated successfully.")

    final_slides = []

    # 2. Process each slide
    for i in range(1, 5):
        print(f"\n--- Processing Slide {i} ---")
        slide_key = f"slide{i}"
        
        # A. Generate the background image
        prompt = data[slide_key]["visual_prompt"]
        bg_image = generate_and_download_image(prompt, i)
        
        # B. Add smart text to the image (Updated to use Gemini text)
        headline = data[slide_key]["headline"]
        body = data[slide_key]["body"]
        print(f"headline={headline}")
        print(f"body={body}")
        
        final_path = create_graphic(bg_image, headline, body, i)
        final_slides.append(final_path)

    print("\n--- Pipeline Finished Locally! ---")
    print(f"Caption: \n{data['caption']}")
    print(f"Final images ready for upload: {final_slides}")

if __name__ == "__main__":
    user_text = input("Enter your topic (e.g., '3 tips for focus'): ")
    run_pipeline(user_text)