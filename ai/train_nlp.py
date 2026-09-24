import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report

import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer


# Download NLTK resources
nltk.download("stopwords")
nltk.download("wordnet")
nltk.download("omw-1.4")


# Load dataset
df = pd.read_csv("dataset/civic_complaints.csv")


# Keep rows with text and category
df = df.dropna(subset=["description", "category_title"])


# Combine title + description
df["text"] = (
    df["title"].fillna("") + " " +
    df["description"].fillna("")
)


# NLTK preprocessing
stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()


def preprocess_text(text):
    words = text.lower().split()

    words = [
        word for word in words
        if word.isalpha() and word not in stop_words
    ]

    words = [
        lemmatizer.lemmatize(word)
        for word in words
    ]

    return " ".join(words)


print("Preprocessing text...")

df["processed_text"] = df["text"].apply(preprocess_text)


# Features and target
# Remove categories with fewer than 2 complaints
category_counts = df["category_title"].value_counts()

df = df[
    df["category_title"].isin(
        category_counts[category_counts >= 2].index
    )
]

# Features and target
# Remove categories with fewer than 2 complaints
category_counts = df["category_title"].value_counts()

df = df[
    df["category_title"].isin(
        category_counts[category_counts >= 2].index
    )
]

# Remove categories with fewer than 2 complaints
category_counts = df["category_title"].value_counts()

df = df[
    df["category_title"].isin(
        category_counts[category_counts >= 2].index
    )
]

# Remove categories with fewer than 2 complaints
category_counts = df["category_title"].value_counts()

df = df[
    df["category_title"].isin(
        category_counts[category_counts >= 2].index
    )
]

# Features and target
X = df["processed_text"]
y = df["category_title"]


# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# TF-IDF + Logistic Regression
model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 2)
        )
    ),
    (
        "classifier",
        LogisticRegression(
            max_iter=1000
        )
    )
])


print("Training NLP model...")
print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))


model.fit(X_train, y_train)

print("Training completed.")


# Evaluate
y_pred = model.predict(X_test)

print("\nClassification Report:")
print(classification_report(y_test, y_pred))
# Save trained NLP model
joblib.dump(model, "ai/models/nlp_category_model.pkl")

print("NLP model saved successfully.")