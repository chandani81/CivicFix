# CivicFix categorization model artifact

This directory contains the trained `svm_categorizer.joblib` pipeline and its
recorded evaluation file, `svm_categorizer.metrics.json`. The object implements
`predict([text])` and returns one CivicFix category:

- `road_damage`
- `water_leakage`
- `garbage`
- `street_light`
- `drainage`
- `others`

To reproduce it, run `python -m ai_services.train_svm` from `backend/`. The
trainer reads the versioned dataset, evaluates the model, and only writes an
artifact when both required accuracy checks pass. Install dependencies from
`requirements.txt` first.

Do not load an artifact from an unknown source: serialized model files can
execute Python code while loading.
