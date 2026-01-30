from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import random
import subprocess
from backend.core.logic import PronunciationTrainer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🚀 Starting Server & Loading AI Model...")
trainer = PronunciationTrainer()

SENTENCES = [
    "The quick brown fox jumps over the lazy dog.",
    "She sells seashells by the seashore.",
    "Artificial intelligence is transforming the world.",
    "I would like to order a cappuccino with oat milk, please.",
    "Can you please tell me the way to the nearest station?",
    "Pronunciation is key to clear communication.",
    "Programming in Python is both fun and powerful."
]

@app.get("/")
def home():
    return {"message": "Pronunciation AI is alive!"}

@app.get("/get-sentence")
def get_sentence():
    text = random.choice(SENTENCES)
    return {"text": text}

@app.post("/analyze")
async def analyze_audio(file: UploadFile = File(...), text: str = Form(...)):
    raw_filename = "temp_raw_audio" 
    clean_filename = "temp_clean.wav" 

    # 1. Save the raw file
    with open(raw_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        # 2. Convert to clean WAV using FFmpeg
        subprocess.run([
            "ffmpeg", "-i", raw_filename, 
            "-ar", "16000", 
            "-ac", "1", 
            "-f", "wav", 
            clean_filename, 
            "-y"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 3. Use the NEW logic flow
        # We only get user phonemes here. 
        # The 'compare' function now handles the target phonemes internally.
        user_phonemes = trainer.get_user_phonemes(clean_filename)
        
        # Pass the RAW TEXT to compare, not phonemes
        score, breakdown = trainer.compare(text, user_phonemes)

        return {
            "score": score,
            "breakdown": breakdown, 
            "user_phonemes": user_phonemes
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return {"error": str(e)}

    finally:
        # Cleanup
        if os.path.exists(raw_filename): os.remove(raw_filename)
        if os.path.exists(clean_filename): os.remove(clean_filename)