from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def main() -> None:
    dataset_path = Path("/app/data/exports/ml_dog_day_dataset.csv")

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    df = pd.read_csv(dataset_path)

    # Target
    target_col = "target_risk_level"

    # Drop columns that should not be used directly for training
    drop_cols = {
        "target_risk_level",
        "target_usage_level",
        "target_flag_count",
        "target_flags",
        "dog_name",
        "date",
    }

    feature_cols = [col for col in df.columns if col not in drop_cols]

    X = df[feature_cols].copy()
    y = df[target_col].copy()

    # Boolean handling
    for col in X.columns:
        if X[col].dtype == bool:
            X[col] = X[col].astype(int)

    categorical_features = [
        col for col in X.columns
        if X[col].dtype == "object"
    ]
    numeric_features = [
        col for col in X.columns
        if col not in categorical_features
    ]

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value=0)),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    multi_class="auto",
                ),
            ),
        ]
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    print(f"Dataset path: {dataset_path}")
    print(f"Rows: {len(df)}")
    print(f"Features used: {len(feature_cols)}")
    print()
    print("Class distribution:")
    print(y.value_counts().to_string())
    print()
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print()
    print("Classification report:")
    print(classification_report(y_test, y_pred))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))

    # Feature importance approximation for logistic regression
    classifier = model.named_steps["classifier"]
    preprocessor_fitted = model.named_steps["preprocessor"]

    feature_names = preprocessor_fitted.get_feature_names_out()
    coef_df = pd.DataFrame(
        classifier.coef_.T,
        index=feature_names,
        columns=classifier.classes_,
    )

    importance_path = Path("/app/data/exports/logistic_feature_coefficients.csv")
    coef_df.to_csv(importance_path)

    print()
    print(f"Feature coefficients saved to: {importance_path}")


if __name__ == "__main__":
    main()