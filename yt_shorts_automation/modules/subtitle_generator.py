import whisper
import os
from moviepy.editor import TextClip, CompositeVideoClip

def generate_subtitles(audio_path: str):
    """
    Transcribes audio using Whisper and returns a list of segments/words.
    """
    if not os.path.exists(audio_path):
        print(f"Audio file not found: {audio_path}")
        return []

    print("Loading Whisper model...")
    model = whisper.load_model("base") # 'base' is a good balance of speed/accuracy
    print("Transcribing audio...")
    result = model.transcribe(audio_path, word_timestamps=True)
    
    # efficient extraction of word-level data if available, otherwise segments
    # The 'word_timestamps=True' might require a specific model or generic return. 
    # 'base' model supports it in newer versions? 
    # If not, we fall back to segments.
    
    segments = result.get('segments', [])
    return segments

def create_subtitle_clips(segments, video_size=(1080, 1920)):
    """
    Creates a list of MoviePy TextClips from transcription segments.
    """
    subtitle_clips = []
    w, h = video_size
    
    for segment in segments:
        start_time = segment['start']
        end_time = segment['end']
        text = segment['text'].strip()
        
        # Create TextClip
        # Note: 'method="caption"' is good for wrapping text.
        # Font might need to be specified if 'Arial' isn't found (e.g. 'calibri' on Windows)
        try:
            txt_clip = TextClip(
                text,
                fontsize=70,
                color='white',
                stroke_color='black',
                stroke_width=2,
                font='Arial-Bold', # Ensure this font exists or use a path
                method='caption',
                size=(w*0.8, None), # 80% width
                align='center'
            ).set_start(start_time).set_end(end_time).set_position(('center', 'center')) # Centered
            
            subtitle_clips.append(txt_clip)
        except Exception as e:
            print(f"Error creating clip for text '{text}': {e}")
            
    return subtitle_clips

if __name__ == "__main__":
    # Test
    # segments = generate_subtitles("output/voiceover.mp3")
    # clips = create_subtitle_clips(segments)
    pass
