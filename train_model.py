import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os
from data_processor import load_and_preprocess_data, extract_features

def train_and_save_model(data_path="voc_calibration_data.csv", model_path="pneumonia_voc_model.pkl"):
    """
    Trains a Random Forest classifier to predict specific VOC compounds based on filtered levels.
    """
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found. Run synthetic_data_gen.py first.")
        return

    print("Loading and preprocessing calibration data...")
    df = load_and_preprocess_data(data_path)
    X, y = extract_features(df)
    
    if y is None:
        print("Error: No labels ('compound') found in data.")
        return

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print("Training Random Forest Classifier on Compound Signatures...")
    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    # Evaluate
    y_pred = clf.predict(X_test)
    print("\nModel Evaluation:")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.2f}")
    print(classification_report(y_test, y_pred))

    # Save model
    joblib.dump(clf, model_path)
    print(f"Voc Model saved successfully to {model_path}")

if __name__ == "__main__":
    train_and_save_model()
