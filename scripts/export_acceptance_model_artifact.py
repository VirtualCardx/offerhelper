from __future__ import annotations

import argparse
import json
import pathlib
import sys
from decimal import Decimal

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.modules.acceptance_prediction.application.exporter import (
    AcceptanceModelArtifactExporter,
    AcceptanceTrainingSample,
)
from src.modules.acceptance_prediction.application.sample_data import build_demo_training_samples
from src.modules.acceptance_prediction.application.training_data import HistoricalAcceptanceTrainingDataService
from src.modules.acceptance_prediction.application.trainer import AcceptanceModelTrainer
from src.shared.infrastructure.db.session import SessionLocal, init_db


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export a standardized acceptance model artifact.")
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "artifacts" / "acceptance_prediction"),
        help="Directory where the manifest and pickle model will be written.",
    )
    parser.add_argument(
        "--model-name",
        default="baseline-offer-acceptance",
        help="Model family name.",
    )
    parser.add_argument(
        "--model-version",
        default="0.4.0",
        help="Model version to export.",
    )
    parser.add_argument(
        "--framework",
        default="xgboost",
        choices=["sklearn", "xgboost"],
        help="Framework label to store in the manifest.",
    )
    parser.add_argument(
        "--source",
        default="demo",
        choices=["demo", "db"],
        help="Training sample source. Use 'db' to export from completed offers in the database.",
    )
    return parser


def main() -> None:
    parser = build_argument_parser()
    args = parser.parse_args()

    exporter = AcceptanceModelArtifactExporter()
    training_samples = _load_training_samples(source=args.source)
    feature_order = [
        "offer_to_market_ratio",
        "raise_ratio",
        "interview_score",
        "has_other_offer",
    ]
    trained_model = AcceptanceModelTrainer().train(
        training_samples=training_samples,
        feature_order=feature_order,
    )
    exported = exporter.export(
        model_name=args.model_name,
        model_version=args.model_version,
        framework=args.framework,
        output_dir=pathlib.Path(args.output_dir),
        feature_order=trained_model.feature_order,
        intercept=trained_model.intercept,
        coefficients=trained_model.coefficients,
        training_samples=training_samples,
        metrics={
            "source": f"{args.source}-trained-export-script",
            "trainingAccuracy": round(trained_model.accuracy, 4),
            "trainingLogLoss": round(trained_model.log_loss, 6),
        },
    )

    print(
        json.dumps(
            {
                "manifestPath": str(exported.manifest_path),
                "modelPath": str(exported.model_path),
                "sampleCount": exported.sample_count,
                "acceptanceRate": str(exported.acceptance_rate),
                "source": args.source,
                "trainingAccuracy": round(trained_model.accuracy, 4),
                "trainingLogLoss": round(trained_model.log_loss, 6),
            }
        )
    )


def _load_training_samples(*, source: str) -> list[AcceptanceTrainingSample]:
    if source == "demo":
        return build_demo_training_samples()
    init_db()
    session = SessionLocal()
    try:
        return HistoricalAcceptanceTrainingDataService(session).build_training_samples()
    finally:
        session.close()


if __name__ == "__main__":
    main()
