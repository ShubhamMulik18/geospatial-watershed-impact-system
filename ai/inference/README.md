AI Inference Handoff
====================

For the source-verified integration handoff and installation instructions, see
[BACKEND_HANDOFF.md](BACKEND_HANDOFF.md), reviewed against AI 6fe036e and backend
07a331f on 2026-10-06. That document distinguishes confirmed AI behavior from the
backend decisions still requiring coordination.

Status
------

The result contract is implemented in contracts.py. A development bundle exporter
is available in ai/training/export_model.py, with a CPU loader in model_loader.py.
One-photo prediction is implemented in predictor.py. The backend prediction
endpoint, persistence adapter and installation on Person 2's machine remain pending.
Software checks do not establish that an export has run successfully on your Mac;
record your actual command results in ai/STATUS.md after running them.

This is the proposed AI-side handoff for Person 2. It was compared with backend
commit a42bfae and AI baseline commit dc1d30f on 2026-10-05. The two database decisions below
remain open; this document does not claim that the teammates have agreed to them.

What each person owns
--------------------

- Person 3 loads the model, processes one photograph and returns PredictionResult.
- Person 2 owns photo paths, request validation, HTTP routes, IDs and database writes.
- Person 1 displays the backend response and its human-review notice.
- Person 4 handles satellite/geospatial processing and report generation.

The contract uses only the Python standard library. It does not perform inference.

Internal result fields
----------------------

| Field | Meaning |
|---|---|
| class_id | Public string ID, such as check_dam, or other_unknown as a fallback |
| predicted_class | Exact display label from classes.json or the exported bundle |
| confidence | Top trained candidate's softmax score, between 0 and 1 |
| requires_verification | Whether a person must review the result |
| top_candidate_class_id | Original top trained candidate, even after fallback |
| threshold | Applied cutoff, or None when no cutoff has been selected |
| model_version | Version identifying the weights and inference settings bundle |
| model_hash | Lowercase SHA-256 of the exact weights file loaded by the model |

A confidence score is not measured accuracy or a calibrated probability of being
correct. For other_unknown it still describes the original candidate; it is not
the probability that the image belongs to an unknown class.

Class labels remain in ai/config/classes.json. Do not create another label list
in the predictor. The bundle must preserve these labels and the exact trained
output order: check_dam, farm_pond, percolation_tank, contour_trench. Other/Unknown
is currently a fallback, not a fifth trained output. Plantation is not included.

The predictor validates its result against the bundle's public labels using
result.validate_labels(labels). Its top candidate comes from the loaded model's
ordered classes, which the loader checks against the bundle's class file.

Review and threshold rules
--------------------------

- None means no threshold was selected. Never replace it silently with 0 or 0.70.
- Without a selected threshold, the contract permits a provisional top candidate
  or other_unknown, but requires human review in both cases.
- With a numeric threshold, a score strictly below it must return other_unknown.
  A score equal to the threshold is not below it.
- Other/Unknown always requires review, and the original candidate is preserved.
- Every result from the current development model must require review, even if
  the team later chooses a provisional cutoff. The predictor must enforce this.
- Threshold validation status belongs in the exported bundle metadata. Supplying
  a number does not establish that it was selected using validation data.
- Unreadable images or missing models are errors, not Other/Unknown predictions.

Public API mapping
------------------

Person 2 can build the existing PredictionResponse from:

```python
payload = {
    "prediction_id": str(prediction_id),
    "photo_id": str(photo_id),
    **result.to_public_fields(),
}
```

The five AI fields are class_id, predicted_class, confidence,
requires_verification and model_version. The current backend forbids extra public
fields. Do not pass result.to_dict() directly into PredictionResponse.

The frontend maps predicted_class to predictedClass, requires_verification to
verificationRequired, and model_version to modelVersion. It receives confidence
on the 0-to-1 scale. Its local warnings array is absent from the current API schema;
Person 1 should derive review notices or agree an explicit schema change.

Open database decisions for Person 2
-----------------------------------

1. The database uses integer label_id, but the AI uses stable string class IDs.
   Define a permanent public class lookup, including other_unknown, or deliberately
   migrate the column. Do not silently reuse model output positions as database IDs.
   In backend commit a42bfae, AnalysisService._build_prediction_snapshot currently
   uses class_id=str(prediction.label_id). Person 2 must use the agreed lookup here
   too, so snapshots contain IDs such as farm_pond rather than a string such as "1".
2. The database requires a numeric threshold; the current bundle stores None.
   The proposed minimal change is a nullable threshold column and migration owned
   by Person 2, preserving None as SQL NULL. No cutoff should be invented: the
   current bundle loader rejects numeric thresholds. This database change remains
   a coordination decision, not an implemented change.

Other database mappings are predicted_class -> predicted_label,
requires_verification -> review_flag and top_candidate_class_id -> top_candidate.
Person 2 stores the model version, hash and score. No database code is added here.

Run the software checks
-----------------------

From the project root:

```bash
.venv-ai/bin/python -m unittest discover -s ai/tests -p 'test_contracts.py' -v
```

The tests use synthetic values. They do not load your checkpoint, use field photos,
train a model, download weights, select a real threshold or measure model accuracy.

Export a development bundle
---------------------------

The exporter needs best.pt and the adjacent metadata.json from the same completed
training run, plus the exact classes.json used during training. It checks their
agreement, loads the saved weights on CPU and retains the original class order.
It does not read the photograph dataset or private manifest. It writes a raw CPU
state_dict, not a pickled model object. Source training files are preserved.

For the first recorded training run, start with this read-only check:

```bash
.venv-ai/bin/python -m ai.training.export_model --checkpoint ai/models/training_runs/dev-20261004T094431Z-bns0tl6u/best.pt --model-version dev-20261005-v1 --check
```

After the check passes, create the bundle:

```bash
.venv-ai/bin/python -m ai.training.export_model --checkpoint ai/models/training_runs/dev-20261004T094431Z-bns0tl6u/best.pt --model-version dev-20261005-v1 --write
```

The output folder is ai/models/bundles/dev-20261005-v1/. It contains:

| File | Purpose |
|---|---|
| model.pt | Exported CPU weights, with a SHA-256 recorded in metadata.json |
| classes.json | Exact public class definitions used for training |
| metadata.json | Ordered trained classes, preprocessing, review policy and provenance |
| MODEL_CARD.md | Recorded data counts, validation scores and development limitations |

Export verifies a reload and compares its synthetic-input logits with the source
checkpoint. An existing bundle folder is never overwritten; use a new version
name for a new export. Interrupted or failed writes remove only their new folder.
Model files remain under the ignored ai/models/ directory. Share the complete
bundle through an agreed team file location; ordinary Git commits contain code
and documentation, not these model files or private photographs.

This first bundle deliberately retains threshold=None and forces human review.
Its explicit development policy is to show the top candidate for review while
the threshold is unset. predictor.py implements that policy. The
database's non-null threshold requirement is still an open Person 2 decision.
Neither export nor loading selects a threshold or performs held-out evaluation.

Check the saved bundle on CPU:

```bash
.venv-ai/bin/python -m ai.inference.model_loader --bundle ai/models/bundles/dev-20261005-v1 --check
```

The loader interface used by the predictor is:

```python
from ai.inference.model_loader import load_model

loaded = load_model(bundle_dir, device="cpu")
# loaded.model returns raw logits. predictor.py applies preprocess_image(),
# torch.inference_mode() and softmax, then builds PredictionResult.
```

The loader uses only bundle files and shared inference code; it does not depend
on training folders, private data or paths from the original Mac. It requires
torch, torchvision and Pillow from the AI environment. Package installation and
a test on Person 2's machine are described in BACKEND_HANDOFF.md; that machine's
installation and full backend integration still need to be checked.

Export/loading tests
--------------------

```bash
.venv-ai/bin/python -m unittest discover -s ai/tests -p 'test_export_model.py' -v
```

These tests create one temporary checkpoint using the actual trainer, random
initialization and synthetic tensors for a single epoch. They exercise export,
CPU reload, preserved outputs, class order, checksums and failure handling. All
fixture files are temporary. This does not retrain or evaluate your saved model.

Predict one photograph
----------------------

The callable interface for Person 2 is now implemented:

```python
from ai.inference.predictor import load_predictor

# Once when the backend starts, using its configured local bundle directory:
predictor = load_predictor(bundle_dir, device="cpu")

# For each request, after the backend resolves photo_id to a stored photo path:
result = predictor.predict(image_path=stored_photo_path)

# Add backend-generated IDs to this public subset for PredictionResponse:
public_fields = result.to_public_fields()
# result.to_dict() contains internal metadata for the persistence adapter.
```

Use the returned predictor for subsequent photographs. Calling load_predictor()
for every request would unnecessarily reload the model. The predictor uses only
inference modules, not training scripts or the private dataset manifest.

For the first manual check, use the farm-pond photograph previously converted to
PNG. This photo belongs to the recorded training split; it checks the code path,
not generalization accuracy. Keep the held-out test set for planned evaluation.

```bash
.venv-ai/bin/python -m ai.inference.predictor --bundle ai/models/bundles/dev-20261005-v1 --image ai/data/processed/farm_pond/farm_pond_0002.png
```

The CLI prints the eight-field internal result as JSON. An unset Python threshold
appears as JSON null. A reminder goes to stderr, leaving stdout usable as JSON.
No result file is created and neither the photo nor model files are changed.

For this bundle, class_id and top_candidate_class_id are the top intervention
candidate, predicted_class is its display label, and requires_verification is
always true. Confidence is an uncalibrated softmax score, not measured accuracy.
A wrong prediction is possible with this very small training collection.

There is no threshold override argument. The current loader rejects numeric
thresholds. Numeric-cutoff fallback logic has a synthetic unit test, but using a
cutoff with a real model needs validation-based selection and an explicit update
to the bundle format/loader. No unknown-class recognition has been established.

Error handling for Person 2:

- Handle bundle/configuration problems when loading the predictor at startup.
- Invalid or missing photographs raise ValueError through the shared preprocessor.
- Unexpected tensor shapes, types or nonfinite model outputs raise RuntimeError.
- Map exceptions to the backend's existing error response; never store a made-up
  successful prediction after an error.
- Keep requires_verification in the public result and immutable analysis snapshot.

The predictor provides no HTTP endpoint, database write, GPS extraction, satellite
analysis or report generation. Person 2's new analysis route requires an existing
stored prediction, so its AI adapter and persistence decisions must be completed
before this code enables that workflow.

Predictor tests
---------------

```bash
.venv-ai/bin/python -m unittest discover -s ai/tests -p 'test_predictor.py' -v
```

These tests use a temporary MobileNetV2 bundle with controlled test weights and
generated images. They check preprocessing, class order, softmax, model reuse,
review rules, errors, unchanged model/files and JSON output. They do not train,
download weights, use field photos or measure watershed classification accuracy.
