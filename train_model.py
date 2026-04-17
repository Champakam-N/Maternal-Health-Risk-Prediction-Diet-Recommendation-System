import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import joblib

# ------------------------------------
# 1. LOAD REAL DATASET
# ------------------------------------
df = pd.read_csv("Maternal Health Risk Data Set.csv")

# Check first few rows (optional)
print("Dataset loaded successfully!")
print(df.head())

# ------------------------------------
# 2. FEATURES & TARGET
# ------------------------------------
X = df[['Age', 'SystolicBP', 'DiastolicBP', 'BS', 'BodyTemp', 'HeartRate']]
y = df['RiskLevel']     # Target column

# ------------------------------------
# 3. LABEL ENCODING (Low, Mid, High)
# ------------------------------------
le = LabelEncoder()
y_enc = le.fit_transform(y)

# ------------------------------------
# 4. BUILD MODEL PIPELINE
# ------------------------------------
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", RandomForestClassifier(
        n_estimators=200,
        random_state=42
    ))
])

# ------------------------------------
# 5. TRAIN MODEL
# ------------------------------------
pipeline.fit(X, y_enc)

# ------------------------------------
# 6. SAVE JOBLIB FILES
# ------------------------------------
joblib.dump(pipeline, "maternal_health_model.joblib")
joblib.dump(list(X.columns), "model_features.joblib")
joblib.dump(le, "label_encoder.joblib")

print("\n Training completed successfully!")
print("Saved:")
print(" - maternal_health_model.joblib")
print(" - model_features.joblib")
print(" - label_encoder.joblib")
