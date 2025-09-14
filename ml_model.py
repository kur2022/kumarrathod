import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# ✅ Train the model using historical stock data
def train_model(df):
    # Ensure required columns exist
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'Target']
    if not all(col in df.columns for col in required_cols):
        raise ValueError("Missing required columns in training data.")

    # Features and target
    X = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    y = df['Target']  # Binary: 1 for upward movement, 0 for downward

    # Scale features for better performance
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42
    )

    # Train Random Forest model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Return model and scaler for prediction
    return model, scaler

# ✅ Predict movement for a new data point
def predict_movement(model, scaler, latest_data):
    # latest_data should be a dictionary with keys: Open, High, Low, Close, Volume
    try:
        input_df = pd.DataFrame([latest_data])
        input_scaled = scaler.transform(input_df)
        prediction = model.predict(input_scaled)[0]
        confidence = model.predict_proba(input_scaled)[0][prediction]
        label = "📈 Predicted Up" if prediction == 1 else "📉 Predicted Down"
        return f"{label} (Confidence: {confidence:.2f})"
    except Exception as e:
        return f"⚠️ Prediction error: {e}"
