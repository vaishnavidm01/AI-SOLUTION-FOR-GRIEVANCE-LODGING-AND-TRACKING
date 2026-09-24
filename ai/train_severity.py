import pandas as pd

# Load dataset
df = pd.read_csv("../dataset/bmc_train.csv")

# Features used for prediction
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

# Keep only required columns
data = df[features + [target]].copy()

# Remove incomplete rows
data = data.dropna()

print("Training data prepared")
print("Rows:", len(data))
print("\nFeatures:")
print(features)

print("\nTarget distribution:")
print(data[target].value_counts())