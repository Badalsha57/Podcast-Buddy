import os
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# Ek level upar jao (..) fir models folder mein jao
model_path = "../models/custom_summarizer"

print(f"Loading model from: {model_path}")

# Local path confirm karne ke liye:
if not os.path.exists(model_path):
    print("ERROR: Model folder nahi mil raha! Check karo ki path sahi hai.")
else:
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_path)

    text = "Artificial Intelligence is changing the world by making healthcare faster and more efficient for everyone."

    inputs = tokenizer(text, return_tensors="pt", max_length=512, truncation=True)
    summary_ids = model.generate(inputs["input_ids"], max_length=50, min_length=5, length_penalty=2.0)

    print("Summary:", tokenizer.decode(summary_ids[0], skip_special_tokens=True))