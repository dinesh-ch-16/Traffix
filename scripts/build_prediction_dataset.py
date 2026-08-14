from prediction.prediction_dataset import (
    PredictionDatasetBuilder
)


INPUT_FILE = (
    "data/processed/traffic_states/"
    "traffic_states_15min.csv"
)


OUTPUT_FILE = (
    "data/processed/predictions/"
    "prediction_dataset.csv"
)


def main():

    builder = PredictionDatasetBuilder(
        input_file=INPUT_FILE,
        output_file=OUTPUT_FILE,
        horizon_seconds=300
    )

    count = builder.build()

    print()
    print("=" * 60)
    print("TRAFFIX PREDICTION DATASET")
    print("=" * 60)

    print(
        f"Prediction horizon : 300 seconds"
    )

    print(
        f"Training samples   : {count}"
    )

    print(
        f"Output             : {OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()