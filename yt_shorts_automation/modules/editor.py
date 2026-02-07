import os
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip
from moviepy.video.fx.all import resize, crop
from modules.subtitle_generator import generate_subtitles, create_subtitle_clips

def assemble_video(video_paths: list, audio_path: str, output_path: str = "output/final_short.mp4"):
    """
    Assembles the final video from clips and audio.
    """
    if not video_paths or not os.path.exists(audio_path):
        print("Missing video clips or audio file.")
        return None

    print("Loading audio...")
    audio_clip = AudioFileClip(audio_path)
    total_duration = audio_clip.duration
    
    print(f"Audio Duration: {total_duration}s")

    clips = []
    current_duration = 0
    
    # Load and process video clips
    for path in video_paths:
        if not os.path.exists(path):
            continue
            
        clip = VideoFileClip(path)
        
        # Resize to 9:16 (1080x1920) logic
        # If the clip is not 9:16, we crop to center.
        target_ratio = 9/16
        clip_ratio = clip.w / clip.h
        
        if clip_ratio > target_ratio:
            # Too wide, crop width
            new_width = clip.h * target_ratio
            clip = crop(clip, x1=(clip.w/2) - (new_width/2), width=new_width, height=clip.h)
        elif clip_ratio < target_ratio:
            # Too tall, crop height (unlikely usually, but possible)
            new_height = clip.w / target_ratio
            clip = crop(clip, y1=(clip.h/2) - (new_height/2), width=clip.w, height=new_height)
            
        # Resize to exactly 1080x1920
        clip = resize(clip, height=1920) 
        # (width will automatically be ~1080, might need slight force resize if rounding errors)
        
        clips.append(clip)
        current_duration += clip.duration
        
        # Stop if we have enough footage (allow a little buffer)
        if current_duration >= total_duration:
            break
            
    if not clips:
        print("No valid clips loaded.")
        return None

    print("Concatenating clips...")
    final_video = concatenate_videoclips(clips, method="compose")
    
    # Trim video to match audio exactly
    final_video = final_video.set_audio(audio_clip)
    final_video = final_video.subclip(0, total_duration)

    print("Generating subtitles...")
    try:
        segments = generate_subtitles(audio_path)
        subtitle_clips = create_subtitle_clips(segments, video_size=final_video.size)
        
        # Overlay subtitles
        final_video = CompositeVideoClip([final_video] + subtitle_clips)
    except Exception as e:
        print(f"Warning: Could not add subtitles. Error: {e}")

    print(f"Writing final video to {output_path}...")
    final_video.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
    
    return output_path

if __name__ == "__main__":
    # Test
    pass
