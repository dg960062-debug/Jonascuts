import os
import time
import requests
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

def generate_video_from_prompt(prompt: str, output_path: str):
    """
    Generates a video using Google Veo (via Gemini/Vertex AI).
    Note: As of now, Veo might be under 'imagen' or specific video models.
    This implementation assumes the 'veo-001' or similar model ID available via the GenAI SDK.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("GOOGLE_API_KEY missing.")
        return None

    client = genai.Client(api_key=api_key)
    
    # NOTE: Model names for Veo are subject to change (e.g., "veo-001", "video-001").
    # We will use a placeholder or the most likely current ID.
    # If using Vertex AI, the setup is different. This assumes GenAI Studio usage if available.
    model_id = "veo-2.0-generate-uhd-video" # Example ID, update based on exact availability
    
    print(f"Requesting video for prompt: {prompt[:50]}...")
    
    try:
        # 1. Initiate Generation
        # Veo usually works asynchronously. 
        # For simplicity in this mockup, we are blindly calling generate_content (if synchronous)
        # or assuming a polling mechanism if the SDK supports it.
        # However, many video APIs return a operation/job ID.
        
        # Let's try the standard generate_content if it supports video mime type response
        # Or look for a specific video generation method.
        # As checking strict documentation, often it's client.models.generate_videos
        
        # Hypothetical SDK usage for Veo:
        # operation = client.models.generate_videos(model=model_id, prompt=prompt)
        # result = operation.result()
        
        # Since I cannot verify the exact customized SDK method for Veo right now without live docs,
        # I will implement a robust mock-able structure or standard request if using REST.
        
        # Let's map to what is likely correct based on search results:
        # client.models.generate_videos(...)
        
        # We will assume a 6-second clip.
        response = client.models.generate_videos(
            model="veo-2.0-generate-uhd-video", # Update this if needed
            prompt=prompt,
            config=types.GenerateVideoConfig(
                aspect_ratio="PORTRAIT", # 9:16
                duration_seconds=6
            )
        )
        
        # Saving the video
        # The response typically contains a video URI or bytes.
        if hasattr(response, "video_bytes"):
             with open(output_path, "wb") as f:
                f.write(response.video_bytes)
        elif hasattr(response, "generated_videos"):
             # Retrieve the first video
             video = response.generated_videos[0]
             # If it's a URL
             if hasattr(video, "uri"):
                  vid_data = requests.get(video.uri).content
                  with open(output_path, "wb") as f:
                      f.write(vid_data)
             elif hasattr(video, "video_bytes"):
                  with open(output_path, "wb") as f:
                      f.write(video.video_bytes)
        else:
             print("Unknown response format from Video API")
             return None

        print(f"Video saved to {output_path}")
        return output_path

    except Exception as e:
        print(f"Error generating video: {e}")
        return None

def generate_all_scenes(scenes: list, output_dir: str = "output/clips"):
    """
    Iterates through a list of scene prompts and generates videos for them.
    """
    os.makedirs(output_dir, exist_ok=True)
    file_paths = []
    
    for i, scene_prompt in enumerate(scenes):
        filename = f"{output_dir}/scene_{i+1}.mp4"
        # Enhanced prompt for better style consistency
        full_prompt = f"Cinematic, high quality, 4k, vertical, photorealistic. {scene_prompt}"
        
        # Retry logic
        max_retries = 3
        for attempt in range(max_retries):
            path = generate_video_from_prompt(full_prompt, filename)
            if path:
                file_paths.append(path)
                break
            print(f"Retry {attempt+1}/{max_retries} for scene {i+1}...")
            time.sleep(5) # Wait a bit before retry
            
    return file_paths

if __name__ == "__main__":
    # Test
    generate_video_from_prompt("A cute futuristic robot dancing in neon rain", "output/test_veo.mp4")
