Person 3 to Person 2: confirmed AI integration handoff
=====================================================

Inspected on 2026-10-06: AI branch commit 6fe036e and backend branch commit
07a331f. The installation files accompanying this handoff are new AI-side files;
they are not present in commit 6fe036e until Person 3 commits them. No backend
files, database schema, model weights, classes or inference behavior were changed.

1. Exact prediction contract
----------------------------

`ai.inference.contracts.PredictionResult` is a frozen, keyword-only dataclass.
`Predictor.predict()` returns this object, not an HTTP response or a dictionary.
`result.to_dict()` returns all eight fields below.

| AI field | Python type | Backend internal contract at 07a331f | Persistence mapping |
|---|---|---|---|
| class_id | str | Same field | Stable string ID; integer label_id mapping is unresolved |
| predicted_class | str | Same field | predicted_label |
| confidence | float | Same field | confidence |
| requires_verification | bool | Same field | review_flag |
| top_candidate_class_id | str | Missing | top_candidate, storing the string class ID |
| threshold | float or None | Missing | threshold; current non-null column is incompatible with None |
| model_version | str | Same field | model_version |
| model_hash | str | Backend allows None; real AI always supplies a string | model_hash |

Confidence is a finite top-candidate softmax score in [0, 1], not measured
accuracy. `model_hash` is the lowercase 64-character SHA-256 of the loaded
`model.pt` bytes. `model_version` identifies the complete inference bundle.
The hash is not a hash of the photograph or the entire bundle.

Person 2's internal adapter record needs to preserve the two missing fields.
Adding nullable/defaulted fields can preserve compatibility with existing mock
callers, but the real adapter must copy all eight AI fields explicitly. It must
not substitute the mock's missing hash or discard the original candidate.

The existing PUBLIC `PredictionResponse` is a different, seven-field schema:

```python
payload = {
    "prediction_id": str(prediction_id),  # backend-generated
    "photo_id": str(photo_id),            # backend-owned
    **result.to_public_fields(),
}
```

`to_public_fields()` returns exactly `class_id`, `predicted_class`, `confidence`,
`requires_verification` and `model_version`. The existing public schema forbids
extras: do not pass the eight-field `to_dict()` result straight into it.
Threshold, original candidate and model hash remain internal persistence data.

2. Exact class mapping
----------------------

Verified against `ai/config/classes.json` and the inference class-order checks:

| Public class_id | Exact display label | Model output index |
|---|---|---|
| check_dam | Check Dam | 0 |
| farm_pond | Farm Pond | 1 |
| percolation_tank | Percolation Tank | 2 |
| contour_trench | Contour Trench | 3 |
| other_unknown | Other/Unknown | None: fallback only |

These indices describe the four model outputs. They are NOT agreed database
label IDs. No integer-to-class registry was found in the inspected backend app.
The backend should preserve the exact string meanings above. If it retains
integer `label_id`, Person 2 must propose and agree an explicit stable lookup;
Person 3 has not assigned those integers. Use the same reverse lookup for API
responses and analysis snapshots. Currently `_build_prediction_snapshot()` uses
`class_id=str(prediction.label_id)`, which does not recover the AI class ID.

`plantation` is removed. The bundle loader explicitly rejects a class file that
contains it. `other_unknown` is not trained and cannot be the top trained
candidate. Runtime labels come from the verified bundle's own `classes.json`.

3. Exact meaning of threshold=None
----------------------------------

For `dev-20261005-v1`, no acceptance cutoff has been selected. The loader checks
the complete development policy and accepts only an unset threshold with forced
review. For every successfully classified photo, including high-scoring photos:

- `threshold` is Python `None`, serialized as JSON `null`.
- `class_id == top_candidate_class_id`: return the top intervention candidate.
- `predicted_class` is that candidate's exact display label.
- `requires_verification` is `True`.

Unset does NOT mean zero. It does NOT mean every photo becomes Other/Unknown.
The current real bundle does not perform threshold-based rejection of unknown
photos. The generic contract and predictor have numeric-cutoff logic tested with
synthetic fixtures, but the current loader rejects numeric-cutoff bundles.

The existing database column is `threshold: Mapped[float]`, `nullable=False`,
both in the model and the original migration. It cannot persist this AI result
unchanged. The smallest proposed change is for Person 2 to coordinate a nullable
threshold column/type and a migration, preserving None as SQL NULL on readback.
This is a proposal, not an applied schema change. Do not insert 0, 0.70 or another
placeholder. If nullability is not agreed, persistence remains blocked.

4. Inference entry point and installation
----------------------------------------

```python
from pathlib import Path
from ai.inference.predictor import load_predictor

# Once per backend process, using a configured absolute local bundle path:
predictor = load_predictor(Path(bundle_directory), device="cpu")

# Per photograph, after the backend resolves its stored photo ID to a local file:
result = predictor.predict(image_path=Path(stored_photo_path))
```

The backend adapter can keep its existing `predict(photo_path: Path)` signature
and forward that path as `image_path`. Reuse the loaded predictor for subsequent
calls. The current inference implementation supports CPU only.

| Runtime file | Responsibility |
|---|---|
| inference/predictor.py | load_predictor(), Predictor.predict(), softmax and result construction |
| inference/contracts.py | PredictionResult and internal/public serialization |
| inference/model_loader.py | load_model(), LoadedModel, bundle integrity and policy checks |
| inference/model.py | WatershedMobileNetV2 architecture, reconstructed without downloading weights |
| inference/preprocess.py | preprocess_image(), orientation/RGB conversion and fixed model preprocessing |

No runtime import requires training scripts, PyYAML, a private manifest, dataset
folders or the original training checkpoint. Inference does not write to the
database, perform GPS extraction, generate IDs, train or download model weights.

New `ai/pyproject.toml` packages only `ai.inference`. The runtime dependencies are
torch 2.14.x, torchvision 0.29.x and Pillow >=12.3,<13; the dependency resolver
must select a compatible torch/torchvision pair. The training requirements file
remains unchanged. Package version `0.1.0.dev1` is separate from model bundle
version `dev-20261005-v1`.

After these AI files are available in Person 2's checkout, activate the intended
backend Python environment. From the repository root, install:

```bash
python -m pip install ./ai
python -m pip check
python -I -c "from ai.inference.predictor import load_predictor; print('AI inference import: PASS')"
```

The package declares Python >=3.12. Local automated checks use Python 3.12.14;
the existing real-model Mac checks used Python 3.13.0. Installation on Person 2's
actual machine and its complete backend dependency environment is still pending.
If pip reports a conflict, resolve it explicitly rather than bypassing it.

Share the COMPLETE existing `ai/models/bundles/dev-20261005-v1/` folder through
the team's agreed model-file location: `model.pt`, `classes.json`, `metadata.json`
and `MODEL_CARD.md`. It is not included in Git or in the Python package. Configure
the receiving machine's local path; the original Mac path is not required.

```bash
python -m ai.inference.model_loader --bundle PATH_TO_BUNDLE --check
python -m ai.inference.predictor --bundle PATH_TO_BUNDLE --image PATH_TO_STORED_PHOTO
```

Replace those two path placeholders with actual local paths. Load/configuration
errors occur at predictor startup. Missing, corrupt or multiframe images raise
`ValueError`; unexpected/nonfinite tensors raise `RuntimeError`. Person 2 maps
errors to the existing backend error mechanism and must not persist a fabricated
successful prediction. A failure is not an Other/Unknown prediction.

5. AI-side changes in this handoff
----------------------------------

No prediction logic or contract change is needed. Added inference-only package
metadata, source-distribution exclusions, package isolation tests and this
confirmed handoff. Added an ignore rule for generated package metadata. Updated
the inference README to point here and remove its obsolete numeric-cutoff option.
None of these changes alters model outputs or chooses a threshold.

6. Tests and their limits
-------------------------

From the repository root in the AI environment:

```bash
.venv-ai/bin/python -m unittest ai.tests.test_contracts ai.tests.test_export_model ai.tests.test_predictor -v
```

Verified locally on 2026-10-06: all 41 passed (12 contract, 15 export/loader,
14 predictor). Environment: Python 3.12.14, torch 2.14.1+cpu, torchvision
0.29.1+cpu, Pillow 12.3.0. These exercise labels, unset-threshold/review rules,
public projection, hash/policy failures, model reuse, valid/invalid photographs
and serialization. Export tests create a temporary synthetic training fixture;
predictor tests use controlled weights and generated images. These are software
checks, not evaluation of the real watershed model.

Package checks use pip, setuptools and wheel as development/test tools:

```bash
.venv-ai/bin/python -m pip install 'setuptools>=68' wheel
.venv-ai/bin/python -m unittest discover -s ai/tests -p 'test_inference_package.py' -v
```

Verified locally on 2026-10-06: both package tests passed (2/2), making 43 passing
AI software tests across the four suites. They build/install a temporary wheel and check that inference runs outside the
repository with no training/data files and no model downloads. They also inspect
wheel/source archives to exclude model files and private data. Neither test is a
backend database test.

A separate read-only check loaded the actual backend 07a331f PredictionResponse
schema: public projections for all four intervention classes passed, and the
three internal-only fields were correctly rejected as extra public fields. This
checked the real schema code; it did not exercise HTTP, persistence or analysis.

The user previously reported 12 contract tests and 14 predictor tests passing on
the Mac, plus a real prediction on a TRAINING photo: farm_pond, confidence
0.4715189039707184, review required, threshold null, version dev-20261005-v1.
That real bundle is not in this checkout, so it was not rerun here. Its reported
weights hash is
`63706912517ab8844b7d216fca48e49f07a4135f293c9d16ef1759219f6b8dec`.

7. Remaining decisions and Person 2 acceptance checks
----------------------------------------------------

Before persisting real AI results, agree the integer-label lookup or a deliberate
alternative representation, the nullable-threshold migration, and preservation
of all eight internal fields. Confirm the bundle delivery location and backend
configuration. No existing API route name for requesting a prediction is assumed
by this handoff; Person 2 owns that choice within the existing architecture.

The current analysis service requires a stored prediction BEFORE creating an
analysis. The current worker also calls AI after creation but discards its return
value. Merely replacing that worker's mock adapter cannot supply the missing
pre-analysis prediction. Smallest workflow change: run and persist AI in the
pre-analysis prediction flow, then let analysis creation snapshot that row.
Person 2 should decide how to remove/avoid the redundant worker call while keeping
the analysis tied to its captured prediction. No worker change was made here.

Person 2's integration tests should verify:

1. An uploaded/stored photo reaches the real adapter and returns all eight fields.
2. Database write/read preserves None, the candidate ID, score, review flag,
   model version/hash and the agreed class mapping; no mock hash or cutoff appears.
3. The seven-field public response passes the actual PredictionResponse schema.
4. Analysis creation uses the persisted prediction and snapshots a stable string
   class ID, the same confidence and the review flag; a missing prediction still
   produces the existing PREDICTION_REQUIRED error.
5. Invalid images and missing/damaged bundles produce errors without creating
   successful prediction rows. Later predictions do not rewrite older snapshots.

Full upload -> inference -> database -> analysis integration remains untested.
Held-out test evaluation remains pending; threshold selection remains pending.
The small dataset and development model do not establish production performance.
Every current prediction requires human verification.
