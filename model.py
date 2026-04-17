"""
model.py
────────
PURPOSE : Train the Random Forest ML model and save it as placement_model.pkl
RUN     : python model.py   (run ONCE before starting app.py)
SUBJECT : AI (Classification) + DSBDA (Data Preprocessing, Feature Engineering)

STEPS INSIDE:
  1. Generate / load dataset
  2. Feature engineering
  3. Train/test split
  4. Train Random Forest
  5. Evaluate accuracy
  6. Save model with pickle
"""

import pandas as pd
import numpy as np
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# ── STEP 1: DATASET ──────────────────────────────────────────────────────────
# If dataset.csv doesn't exist, we auto-generate 800 realistic rows.
# In a real project you'd replace this with actual placement data.

if not os.path.exists("dataset.csv"):
    np.random.seed(42)
    n = 800

    cgpa          = np.round(np.random.uniform(5.0, 10.0, n), 2)
    internships   = np.random.randint(0, 4, n)
    projects      = np.random.randint(0, 6, n)
    aptitude      = np.round(np.random.uniform(30, 100, n), 1)
    communication = np.round(np.random.uniform(30, 100, n), 1)

    # Placement rule (realistic): good CGPA + apt + comm → placed
    score = (
        (cgpa / 10) * 40 +
        (aptitude / 100) * 30 +
        (communication / 100) * 20 +
        (internships / 3) * 5 +
        (projects / 5) * 5
    )
    # Add 12% random noise to make it non-trivial
    noise = np.random.normal(0, 5, n)
    placed = (score + noise > 55).astype(int)

    df = pd.DataFrame({
        "cgpa": cgpa, "internships": internships, "projects": projects,
        "aptitude": aptitude, "communication": communication, "placed": placed
    })
    df.to_csv("dataset.csv", index=False)
    print(f"✅ Generated dataset.csv  ({n} rows, {placed.sum()} placed)")
else:
    df = pd.read_csv("dataset.csv")
    print(f"✅ Loaded dataset.csv  ({len(df)} rows)")

# ── STEP 2: FEATURES & LABELS ─────────────────────────────────────────────────
X = df[["cgpa", "internships", "projects", "aptitude", "communication"]]
y = df["placed"]

# ── STEP 3: TRAIN/TEST SPLIT ──────────────────────────────────────────────────
# 80% training data, 20% test data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# ── STEP 4: TRAIN RANDOM FOREST ───────────────────────────────────────────────
# WHY Random Forest? (Viva answer)
#   • Builds 100 decision trees on random subsets of data
#   • Final prediction = majority vote of all 100 trees
#   • Much more accurate than a single Decision Tree
#   • Handles non-linear patterns and noisy data well
#   • Gives feature_importances_ which shows which factors matter most

model = RandomForestClassifier(
    n_estimators = 100,    # 100 trees
    max_depth    = 8,      # limit tree depth to prevent overfitting
    random_state = 42
)
model.fit(X_train, y_train)

# ── STEP 5: EVALUATE ──────────────────────────────────────────────────────────
preds = model.predict(X_test)
acc   = accuracy_score(y_test, preds)
print(f"\n📊 Model Accuracy: {acc * 100:.2f}%")
print("\nClassification Report:")
print(classification_report(y_test, preds, target_names=["Not Placed", "Placed"]))

# Print feature importances (DSBDA insight)
print("\n📌 Feature Importances:")
for feat, imp in zip(X.columns, model.feature_importances_):
    print(f"  {feat:>15} : {imp:.4f}")

# ── STEP 6: SAVE MODEL ────────────────────────────────────────────────────────
# pickle converts the Python object to binary file
# app.py loads this once at startup — no retraining needed every request
pickle.dump(model, open("placement_model.pkl", "wb"))
print("\n✅ Model saved as placement_model.pkl")