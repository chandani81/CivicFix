"""Train and verify CivicFix's text categorization SVM.

Run from backend/ with:
    python -m ai_services.train_svm
"""

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, classification_report

from .svm_features import CivicSignalAugmenter


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = BASE_DIR / "training_data" / "civic_issue_categories.csv"
DEFAULT_MODEL = BASE_DIR / "model_artifacts" / "svm_categorizer.joblib"
VALID_CATEGORIES = {
    "road_damage",
    "water_leakage",
    "garbage",
    "street_light",
    "drainage",
    "others",
}

def load_dataset(path):
    texts, labels = [], []
    with Path(path).open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            text = row["text"].strip()
            label = row["category"].strip()
            if not text or label not in VALID_CATEGORIES:
                raise ValueError(f"Invalid training row: {row}")
            texts.append(text)
            labels.append(label)
    if len(set(texts)) != len(texts):
        raise ValueError("Training data contains duplicate text rows.")
    counts = Counter(labels)
    missing = VALID_CATEGORIES - counts.keys()
    if missing or min(counts.values(), default=0) < 10:
        raise ValueError(f"Dataset must contain at least 10 examples per category: {counts}")
    return texts, labels, counts


def build_pipeline():
    features = FeatureUnion(
        [
            (
                "words",
                Pipeline(
                    [
                        ("domain_signals", CivicSignalAugmenter()),
                        (
                            "tfidf",
                            TfidfVectorizer(
                                lowercase=True,
                                ngram_range=(1, 2),
                                sublinear_tf=True,
                                strip_accents="unicode",
                            ),
                        ),
                    ]
                ),
            ),
            (
                "characters",
                TfidfVectorizer(
                    analyzer="char_wb",
                    lowercase=True,
                    ngram_range=(3, 5),
                    sublinear_tf=True,
                    min_df=2,
                ),
            ),
        ]
    )
    return Pipeline(
        [
            ("features", features),
            ("classifier", LinearSVC(C=1.5, class_weight="balanced", random_state=42)),
        ]
    )


def train(dataset_path=DEFAULT_DATASET, model_path=DEFAULT_MODEL, minimum_score=0.80):
    texts, labels, counts = load_dataset(dataset_path)
    train_texts, test_texts, train_labels, test_labels = train_test_split(
        texts,
        labels,
        test_size=0.25,
        random_state=42,
        stratify=labels,
    )
    candidate = build_pipeline()
    candidate.fit(train_texts, train_labels)
    predictions = candidate.predict(test_texts)
    holdout_accuracy = accuracy_score(test_labels, predictions)
    cv_scores = cross_val_score(build_pipeline(), texts, labels, cv=5, scoring="accuracy")
    cv_mean = float(cv_scores.mean())

    print(classification_report(test_labels, predictions, zero_division=0))
    print(f"Holdout accuracy: {holdout_accuracy:.3f}")
    print(f"5-fold accuracy: {cv_mean:.3f} ({', '.join(f'{score:.3f}' for score in cv_scores)})")
    if holdout_accuracy < minimum_score or cv_mean < minimum_score:
        raise RuntimeError(
            f"Model quality below {minimum_score:.0%}; artifact was not written."
        )

    final_model = build_pipeline().fit(texts, labels)
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_model, model_path)
    metrics = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "training_examples": len(texts),
        "class_counts": dict(sorted(counts.items())),
        "holdout_accuracy": round(float(holdout_accuracy), 4),
        "cross_validation_accuracy": round(cv_mean, 4),
        "cross_validation_scores": [round(float(score), 4) for score in cv_scores],
        "model": "TF-IDF word/character features with LinearSVC",
    }
    metrics_path = model_path.with_suffix(".metrics.json")
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(f"Saved model: {model_path}")
    print(f"Saved metrics: {metrics_path}")
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--output", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--minimum-score", type=float, default=0.80)
    args = parser.parse_args()
    train(args.dataset, args.output, args.minimum_score)


if __name__ == "__main__":
    main()
