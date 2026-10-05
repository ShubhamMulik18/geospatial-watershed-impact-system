AI Inference Handoff
====================

Status
------

The result contract is implemented in contracts.py. The model bundle exporter,
loader, predictor and backend prediction endpoint are still future work.

This is the proposed AI-side handoff for Person 2. It was compared with backend
commit c663c78 and AI commit e5e974a on 2026-10-05. The two database decisions below
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

The future predictor must validate its result against the bundle's public labels
using result.validate_labels(labels). The bundle loader must also verify that the
candidate belongs to the ordered trained classes. Contract string checks alone
cannot establish class membership or confirm that a model hash matches a file.

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
2. The database requires a numeric threshold; the current checkpoint stores None.
   Either support an unset threshold in the database, or explicitly agree and
   record a development-only numeric cutoff. Do not invent a validated cutoff.

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
