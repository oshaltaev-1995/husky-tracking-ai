from pathlib import Path

from app.db.session import SessionLocal
from app.services.ml_dataset_service import build_ml_dataset


def main() -> None:
    output_path = Path("/app/data/exports/ml_dog_day_dataset.csv")

    db = SessionLocal()
    try:
        df = build_ml_dataset(
            db=db,
            output_path=output_path,
            hard_day_km_threshold=10.0,
        )
        print(f"ML dataset saved to: {output_path}")
        print(f"Rows: {len(df)}")
        print(f"Columns: {len(df.columns)}")
        print("Target risk distribution:")
        print(df["target_risk_level"].value_counts(dropna=False).to_string())
        print("Target usage distribution:")
        print(df["target_usage_level"].value_counts(dropna=False).to_string())
    finally:
        db.close()


if __name__ == "__main__":
    main()