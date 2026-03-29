from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


def train_and_report(model_name: str, model, X_train, X_test, y_train, y_test, feature_cols_count: int) -> None:
    pipeline = Pipeline(
        steps=[
            ("preprocessor", PREPROCESSOR),
            ("classifier", model),
        ]
    )

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    print("=" * 80)
    print(model_name)
    print("=" * 80)
    print(f"Features used: {feature_cols_count}")
    print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
    print()
    print("Classification report:")
    print(classification_report(y_test, y_pred))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))
    print()


def main() -> None:
    dataset_path = Path("/app/data/exports/ml_next_day_dog_dataset.csv")

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    df = pd.read_csv(dataset_path)

    target_col = "target_next_day_risk_level"

    drop_cols = {
        "target_next_day_risk_level",
        "target_next_day_usage_level",
        "target_next_day_flag_count",
        "target_next_day_flags",
        "dog_name",
        "date",
        "target_date",
    }

    feature_cols = [col for col in df.columns if col not in drop_cols]

    X = df[feature_cols].copy()
    y = df[target_col].copy()

    for col in X.columns:
        if X[col].dtype == bool:
            X[col] = X[col].astype(int)

    categorical_features = [col for col in X.columns if X[col].dtype == "object"]
    numeric_features = [col for col in X.columns if col not in categorical_features]

    global PREPROCESSOR
    PREPROCESSOR = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="constant", fill_value=0)),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            ),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_features,
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

    print(f"Dataset path: {dataset_path}")
    print(f"Rows: {len(df)}")
    print("Target distribution:")
    print(y.value_counts().to_string())
    print()

    train_and_report(
        "Logistic Regression (next-day risk)",
        LogisticRegression(max_iter=2000, multi_class="auto"),
        X_train,
        X_test,
        y_train,
        y_test,
        len(feature_cols),
    )

    train_and_report(
        "Gradient Boosting (next-day risk)",
        GradientBoostingClassifier(random_state=42),
        X_train,
        X_test,
        y_train,
        y_test,
        len(feature_cols),
    )


if __name__ == "__main__":
    main()