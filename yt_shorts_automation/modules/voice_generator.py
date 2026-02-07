import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def generate_voice(text: str, output_path: str = "output/voiceover.mp3"):
    """
    Generates a voiceover from text using OpenAI's TTS API.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Fallback or error - simplistic for now
        print("OPENAI_API_KEY not set. Cannot generate voice.")
        return None

    client = OpenAI(api_key=api_key)

    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx", # Deep and narrated tone
            input=text
        )
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        response.stream_to_file(output_path)
        print(f"Audio saved to {output_path}")
        return output_path
    
    except Exception as e:
        print(f"Error generating voice: {e}")
        return None

if __name__ == "__main__":
    generate_voice("¿Sabías que los pulpos tienen tres corazones? Es algo fascinante.")
