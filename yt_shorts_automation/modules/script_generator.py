import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def generate_script(topic: str):
    """
    Generates a script for a 60-second YouTube Short based on the topic.
    Returns a JSON object with hook, body, outro, and scenes.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are an expert YouTube Shorts scriptwriter. Create a viral script for a 60-second video about: "{topic}".
    
    The script must be in SPANISH.
    
    Structure the response strictly as a JSON object with the following keys:
    - "hook": A catchy opening sentence (approx 3-5 seconds).
    - "body": The main interesting facts, broken down into a flow that retains attention.
    - "outro": A short call to action or closing remark.
    - "scenes": A list of exactly 6-8 distinct visual descriptions (prompts) for a video generation AI. 
      Each scene prompt should be highly descriptive, visual, and suitable for a video generation model like Google Veo. 
      Include camera movement, lighting, and subject details.
    
    Make sure the total reading time of hook + body + outro is around 50-60 seconds.
    The "scenes" should correspond to segments of the script.
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    try:
        script_data = json.loads(response.text)
        return script_data
    except json.JSONDecodeError:
        print("Error decoding JSON from Gemini response.")
        return None

if __name__ == "__main__":
    # Test
    res = generate_script("Curiosidades sobre los pulpos")
    print(json.dumps(res, indent=2, ensure_ascii=False))
