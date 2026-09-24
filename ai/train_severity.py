import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report


# Load dataset
df = pd.read_csv("../dataset/bmc_train.csv")

# Features available when a complaint is submitted
features = [
    "complaint_category",
    "complaint_time_of_day",
    "ward_type",
    "population_density",
    "ward_slum_percentage",
    "has_photo_evidence",
    "has_gps_location",
    "media_attention",
    "repeat_complainant",
    "prior_complaints_count"
]

target = "severity"

# Prepare data
data = df[features + [target]].dropna()

X = data[features]
y = data[target]

# Categorical features
categorical_features = [
    "complaint_category",
    "complaint_time_of_day",
    "ward_type",
    "population_density"
]

# Numerical features
numerical_features = [
    "ward_slum_percentage",
    "has_photo_evidence",
    "has_gps_location",
    "media_attention",
    "repeat_complainant",
    "prior_complaints_count"
]

# Convert categorical values into numbers
preprocessor = ColumnTransformer(
    transformers=[
        (
            "categorical",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_features
        ),
        (
            "numerical",
            "passthrough",
            numerical_features
        )
    ]
)

# Random Forest classifier
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)

# Combine preprocessing + model
pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", model)
])

# Training/testing split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("Training model...")
print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))

# Train
pipeline.fit(X_train, y_train)

print("Training completed.")

# Test
y_pred = pipeline.predict(X_test)

print("\nClassification Report:")
print(classification_report(y_test, y_pred))