import os
import json
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    DataCollatorForSeq2Seq
)
from datasets import Dataset

# Model Configuration
MODEL_NAME = "facebook/bart-base"
SAVE_PATH = "./models/custom_summarizer"
DATA_FILE = "data.json"


def get_training_dataset():
    # Ab ye function direct tumhari data.json file read karega
    if not os.path.exists(DATA_FILE):
        raise FileNotFoundError(f"{DATA_FILE} nahi mili! Pehle data generate karo.")

    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return Dataset.from_list(data)


def train():
    print(f"Loading {MODEL_NAME} for CPU training...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

    dataset = get_training_dataset()

    def preprocess_function(examples):
        model_inputs = tokenizer(examples["article"], max_length=512, truncation=True)
        # Naye versions ke liye 'text_target' zaroori hai
        labels = tokenizer(text_target=examples["summary"], max_length=128, truncation=True)
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    # Map the dataset
    tokenized_datasets = dataset.map(preprocess_function, batched=True)

    training_args = TrainingArguments(
        output_dir="./results",
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        num_train_epochs=3,
        learning_rate=2e-5,
        save_strategy="epoch",
        use_cpu=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets,
        data_collator=DataCollatorForSeq2Seq(tokenizer, model=model),
    )

    print(f"Training started with {len(dataset)} examples...")
    trainer.train()

    # Save model
    model.save_pretrained(SAVE_PATH)
    tokenizer.save_pretrained(SAVE_PATH)
    print(f"Training complete! Model saved in {SAVE_PATH}")


if __name__ == "__main__":
    train()