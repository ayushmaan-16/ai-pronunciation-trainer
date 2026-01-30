from backend.core.logic import PronunciationTrainer
import os

if __name__ == "__main__":
    # 1. Initialize the Brain
    trainer = PronunciationTrainer()

    # 2. Define inputs
    TEXT = "The quick brown fox jumps over the lazy dog"
    # We will need a real file here shortly
    AUDIO_FILE = "test_audio.wav" 

    print(f"\n--- 1. Testing Target Generation ---")
    target_ipa = trainer.get_target_phonemes(TEXT)
    print(f"Text: {TEXT}")
    print(f"Target Phonemes: /{target_ipa}/")

    # Only run audio test if file exists
    if os.path.exists(AUDIO_FILE):
        print(f"\n--- 2. Testing Audio Recognition ---")
        user_ipa = trainer.get_user_phonemes(AUDIO_FILE)
        print(f"User Phonemes:   /{user_ipa}/")

        print(f"\n--- 3. Testing Scoring ---")
        score, mistakes = trainer.compare(target_ipa, user_ipa)
        print(f"📊 Score: {score}%")
        print("⚠️ Mistakes:", mistakes)
    else:
        print(f"\n⚠️ Skipping Audio Test: '{AUDIO_FILE}' not found.")
        print("To test fully, record yourself saying 'The quick brown fox',")
        print("save it as 'test_audio.wav', and drag it into this folder.")