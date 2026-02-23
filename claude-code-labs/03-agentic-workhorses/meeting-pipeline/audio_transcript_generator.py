import asyncio
import edge_tts
from pydub import AudioSegment # pip install pydub

async def make_meeting():
    lines = [
        ("Karthika", "en-IN-NeerjaNeural", "Alright everyone, let's look at the latency spike."),
        ("Alex", "en-US-GuyNeural", "I'm seeing high Kafka lag in the worker pods."),
        ("Jordan", "en-GB-LibbyNeural", "I'll update the stakeholders immediately.")
    ]
    
    file_paths = []
    for name, voice, text in lines:
        path = f"{name}.mp3"
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(path)
        file_paths.append(path)
    
    # --- Stitching them together ---
    print("Combining voices into a single meeting...")
    combined = AudioSegment.empty()
    for path in file_paths:
        audio_clip = AudioSegment.from_mp3(path)
        # Add a 500ms (0.5s) silence between speakers for realism
        combined += audio_clip + AudioSegment.silent(duration=500)
    
    combined.export("meeting_sync.mp3", format="mp3")
    print("Done! 'meeting_sync.mp3' is ready for your app.")

if __name__ == "__main__":
    asyncio.run(make_meeting())