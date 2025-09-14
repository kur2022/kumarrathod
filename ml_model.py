import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
from mlxtend.evaluate import accuracy_score

# ✅ Train multiple models using historical stock data
def train_models(df):
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'Target']
    if not all(col in df.columns for col in required_cols):
        raise ValueError("Missing required columns in training data.")

    X = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    y = df['Target']

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )

    models = {
        "RandomForest": RandomForestClassifier(n_estimators=100, random_state=42),
        "XGBoost": XGBClassifier(use_label_encoder=False, eval_metric='logloss'),
        "LightGBM": LGBMClassifier(),
        "CatBoost": CatBoostClassifier(verbose=0)
    }

    trained_models = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        acc = accuracy_score(y_test, model.predict(X_test))
        trained_models[name] = {
            "model": model,
            "accuracy": acc
        }

    return trained_models, scaler

# ✅ Predict movement using selected model
def predict_movement(trained_models, scaler, latest_data, model_name="RandomForest"):
    try:
        input_df = pd.DataFrame([latest_data])
        input_scaled = scaler.transform(input_df)

        model = trained_models[model_name]["model"]
        prediction = model.predict(input_scaled)[0]
        confidence = model.predict_proba(input_scaled)[0][prediction]
        label = "📈 Predicted Up" if prediction == 1 else "📉 Predicted Down"
        return f"{label} (Confidence: {confidence:.2f}, Model: {model_name})"
    except Exception as e:
        return f"⚠️ Prediction error: {e}"
