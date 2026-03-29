from pathlib import Path

from app.db.session import SessionLocal
from app.services.ml_next_day_dataset_service import build_next_day_ml_dataset


def main() -> None:
    output_path = Path("/app/data/exports/ml_next_day_dog_dataset.csv")

    db = SessionLocal()
    try:
        df = build_next_day_ml_dataset(
            db=db,
            output_path=output_path,
            hard_day_km_threshold=10.0,
        )
        print(f"Next-day ML dataset saved to: {output_path}")
        print(f"Rows: {len(df)}")
        print(f"Columns: {len(df.columns)}")
        print("Target next-day risk distribution:")
        print(df["target_next_day_risk_level"].value_counts(dropna=False).to_string())
        print("Target next-day usage distribution:")
        print(df["target_next_day_usage_level"].value_counts(dropna=False).to_string())
    finally:
        db.close()


if __name__ == "__main__":
    main()