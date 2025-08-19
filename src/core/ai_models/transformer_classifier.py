# module_1_transformer_classifier.py
# pip install torch transformers datasets scikit-learn

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset
from sklearn.model_selection import train_test_split

class SentimentClassifier:
    """A wrapper for a Hugging Face Transformer model for sentiment classification."""
    def __init__(self, model_name="distilbert-base-uncased", num_labels=3):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=num_labels)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)

    def _tokenize_data(self, data):
        return self.tokenizer(data["text"], padding="max_length", truncation=True)

    def fit(self, texts, labels, training_args=None):
        if training_args is None:
            training_args = TrainingArguments(
                output_dir="./transformer_results",
                num_train_epochs=1,  # keep small for demo
                per_device_train_batch_size=8,
                logging_dir='./transformer_logs',
                logging_steps=10,
                evaluation_strategy="epoch"
            )

        train_texts, val_texts, train_labels, val_labels = train_test_split(texts, labels, test_size=0.2, random_state=42)
        train_dataset = Dataset.from_dict({"text": train_texts, "label": train_labels})
        val_dataset = Dataset.from_dict({"text": val_texts, "label": val_labels})

        tokenized_train_ds = train_dataset.map(self._tokenize_data, batched=True)
        tokenized_val_ds = val_dataset.map(self._tokenize_data, batched=True)

        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=tokenized_train_ds,
            eval_dataset=tokenized_val_ds
        )
        print("Starting model finetuning...")
        trainer.train()
        print("Finetuning complete.")

    def predict(self, texts):
        self.model.eval()
        inputs = self.tokenizer(texts, return_tensors="pt", padding=True, truncation=True).to(self.device)
        with torch.no_grad():
            logits = self.model(**inputs).logits
        predicted_class_ids = torch.argmax(logits, dim=-1).cpu().tolist()
        probabilities = torch.softmax(logits, dim=-1).cpu().tolist()
        return predicted_class_ids, probabilities

if __name__ == "__main__":
    sample_texts = [
        "Company XYZ reports record profits, stock soars.",
        "Unexpected Fed rate hike sends markets tumbling.",
        "Analysts remain neutral on the tech sector amid uncertainty.",
        "New product launch from ABC Inc. receives rave reviews.",
        "Regulatory probe into Bank Corp causes stock to plummet."
    ]
    # Labels: 0=Negative, 1=Neutral, 2=Positive
    sample_labels = [2, 0, 1, 2, 0]

    sentiment_model = SentimentClassifier(num_labels=3)
    sentiment_model.fit(sample_texts * 2, sample_labels * 2)  # tiny demo training
    new_headlines = [
        "Market expects strong earnings report from a major retailer.",
        "Inflation fears are growing, potentially impacting consumer spending."
    ]
    predictions, probs = sentiment_model.predict(new_headlines)
    for i, headline in enumerate(new_headlines):
        print(f"Headline: '{headline}' -> Pred ID: {predictions[i]}, Probs: {probs[i]}")
