import os 
import time
from modules.script_generator import generate_script
from modules.voice_generator import generate_voice
from modules.video_generator import generate_all_scenes
from modules.editor import assemble_video
from modules.uploader import upload_video
from dotenv import load_dotenv

load_dotenv()

def main():
    print("--- YouTube Shorts Automation by Google Gemini ---")
    
    # 1. Input Topic
    topic = input("Enter a topic for the Short: ")
    if not topic:
        print("Topic is required.")
        return

    # 2. Generate Script
    print("\n[1/5] Generating Script...")
    script_data = generate_script(topic)
    if not script_data:
        print("Failed to generate script.")
        return
    
    print(f"Title Hook: {script_data.get('hook')}")
    full_text = f"{script_data.get('hook')} {script_data.get('body')} {script_data.get('outro')}"
    print(f"Full Text: {full_text}")

    # 3. Generate Audio
    print("\n[2/5] Generating Voiceover...")
    audio_path = generate_voice(full_text)
    if not audio_path:
        print("Failed to generate audio.")
        return

    # 4. Generate Videos
    print("\n[3/5] Generating Video Clips (Veo)...")
    scenes = script_data.get("scenes", [])
    if not scenes:
        print("No scenes found in script.")
        return
        
    video_clips = generate_all_scenes(scenes)
    if not video_clips:
        print("Failed to generate video clips.")
        return

    # 5. Edit Video
    print("\n[4/5] Assembling Video...")
    final_video_path = assemble_video(video_clips, audio_path)
    if not final_video_path:
        print("Failed to assemble video.")
        return

    # 6. Upload
    print("\n[5/5] Submitting to YouTube...")
    upload_choice = input("Do you want to upload this video? (y/n): ").lower()
    if upload_choice == 'y':
        # Generate tags from topic
        tags = [topic, "shorts", "viral", "curiosities", "ai generated"]
        upload_video(
            final_video_path, 
            title=f"{topic} #Shorts", 
            description=full_text, 
            tags=tags
        )
    else:
        print(f"Video saved locally at: {final_video_path}")

    print("\nDone!")

if __name__ == "__main__":
    main()
