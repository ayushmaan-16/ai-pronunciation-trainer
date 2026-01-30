import torch
import librosa
import numpy as np
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
from phonemizer import phonemize
import Levenshtein
import re

class PronunciationTrainer:
    def __init__(self):
        print("⏳ Loading AI Model...")
        self.model_id = "facebook/wav2vec2-lv-60-espeak-cv-ft"
        self.processor = Wav2Vec2Processor.from_pretrained(self.model_id)
        self.model = Wav2Vec2ForCTC.from_pretrained(self.model_id)
        print("✅ Model Loaded!")

    def clean_phonemes(self, phoneme_str):
        # Remove stress markers and simplify chars
        cleaned = re.sub(r"[ˈˌː]", "", phoneme_str)
        mappings = [
            ('ɹ', 'r'), ('ɾ', 't'), ('i', 'ɪ'), ('u', 'ʊ'),
            ('ə', 'ʌ'), ('ɜ', 'ə'), ('ɛ', 'e'), ('ɔ', 'o'),
            ('ɑ', 'a'), ('ɡ', 'g'),
        ]
        for original, replacement in mappings:
            cleaned = cleaned.replace(original, replacement)
        return cleaned.strip()

    def get_user_phonemes(self, audio_path):
        # Load, Trim Silence, Predict
        speech_array, sr = librosa.load(audio_path, sr=16000)
        non_silent_audio, _ = librosa.effects.trim(speech_array, top_db=20)
        
        inputs = self.processor(non_silent_audio, return_tensors="pt", sampling_rate=16000)
        with torch.no_grad():
            logits = self.model(inputs.input_values).logits

        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = self.processor.batch_decode(predicted_ids)
        return self.clean_phonemes(transcription[0]).replace(" ", "")

    # --- NEW: Word-Level Analysis ---
    def compare(self, text, user_phonemes):
        # 1. Get Target Phonemes per Word
        # We split the text into words first, then phonemize each word individually
        words = text.split()
        target_phonemes_per_word = []
        
        for word in words:
            # Phonemize the single word
            raw_phoneme = phonemize(word, language='en-us', backend='espeak', strip=True)
            clean_phoneme = self.clean_phonemes(raw_phoneme).replace(" ", "")
            target_phonemes_per_word.append(clean_phoneme)

        # 2. Join them to make the full target string
        full_target_string = "".join(target_phonemes_per_word)
        
        # 3. Align the User String to the Target String
        # We use Levenshtein editops to find WHERE the errors are
        edits = Levenshtein.editops(full_target_string, user_phonemes)
        
        # 4. Map errors back to words
        # We need to know: Index 0-3 is "The", Index 4-8 is "Quick", etc.
        word_indices = []
        current_index = 0
        for i, ph in enumerate(target_phonemes_per_word):
            end_index = current_index + len(ph)
            word_indices.append((current_index, end_index, words[i]))
            current_index = end_index

        # Create a set of "bad" indices in the target string
        error_indices = set()
        for action, src_idx, dest_idx in edits:
            if action in ['replace', 'delete']:
                error_indices.add(src_idx)

        # 5. Build the Report
        breakdown = []
        total_score = 0
        
        for start, end, word in word_indices:
            # Check if any error occurred in this word's range
            mistakes_in_word = 0
            length = end - start
            if length == 0: continue # Skip empty phonemes

            for i in range(start, end):
                if i in error_indices:
                    mistakes_in_word += 1
            
            # Calculate word accuracy
            word_accuracy = max(0, (length - mistakes_in_word) / length) * 100
            total_score += word_accuracy
            
            status = "Good" if word_accuracy >95 else "Needs Work"
            breakdown.append({
                "word": word,
                "accuracy": round(word_accuracy),
                "status": status
            })

        final_score = round(total_score / len(words)) if words else 0
        
        return final_score, breakdown