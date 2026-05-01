from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv
import requests

load_dotenv()

api_key = os.getenv("GENAI_APIKEY")
client = genai.Client(api_key=api_key)

def get_clean_json(raw_response_string):
    # Step A: Convert the raw STRING into a dictionary
    full_dict = json.loads(raw_response_string)
    
    # Step B: Extract the nested 'text' string using proper indexing [0]
    inner_json_str = full_dict['candidates'][0]['content']['parts'][0]['text']
    
    # Step C: Clean markdown only. 
    # DO NOT replace '\\' here, or json.loads will fail on the inner string.
    clean_inner = inner_json_str.replace('```json', '').replace('```', '').strip()
    
    # Step D: Convert the inner string to a dictionary
    inner_dict = json.loads(clean_inner)
    
    # Step E: Now clean the actual text content of newlines/slashes
    return deep_clean_text(inner_dict)

def deep_clean_text(data):
    if isinstance(data, dict):
        return {k: deep_clean_text(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [deep_clean_text(v) for v in data]
    elif isinstance(data, str):
        return data.replace('\n', ' ').replace('\\', '').strip()
    return data

def generate_carousel_content(raw_text):
    
    prompt = f"""
    Analyze the following text and create 1 heading slide and 3 structured slides for an Instagram carousel. 
    For 1st slide, I need:
    1. 'visual_prompt': A detailed description for an image generator (like SDXL).
    2. 'headline': A short (1-10 words), catchy title for the presentation.
    For next slides, I need:
    1. 'visual_prompt': A detailed description for an image generator (like SDXL).
    2. 'headline': A short (1-6 words), catchy title for the slide.
    3. 'body': An explanation (40-50 words) summary of the key point.

    Also, write a short, engaging Instagram caption with hashtags.
    
    Return the response ONLY in this JSON format:
    {{
        "slide1": {{ "visual_prompt": "...", "headline": "...", "body": ""}},
        "slide2": {{ "visual_prompt": "...", "headline": "...", "body": "..." }},
        "slide3": {{ "visual_prompt": "...", "headline": "...", "body": "..." }},
        "slide4": {{ "visual_prompt": "...", "headline": "...", "body": "..." }},
        "caption": "..."
    }}

    Input Text: {raw_text}
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-flash-preview:generateContent?key={api_key}"
    payload = json.dumps({
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
        "temperature": 1,
        "maxOutputTokens": 4000
        }
    })
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    # FIX: Check if request was successful
    if response.status_code == 200:
        # FIX: Pass response.text (the STRING), not response.json()
        return get_clean_json(response.text)
    else:
        return f"Error: {response.status_code} - {response.text}"