Watershed Photo Dataset Guide

1. Purpose

This dataset will train an AI model to recognise watershed interventions
from field photographs.

Each training photograph needs a verified label. When the application
is running, the trained model will predict the label automatically.

The public class definitions are stored in:
ai/config/classes.json

2. Public Classes

| Class ID | Display Label |
|---|---|
| check_dam | Check Dam |
| farm_pond | Farm Pond |
| percolation_tank | Percolation Tank |
| contour_trench | Contour Trench |
| plantation | Plantation |
| other_unknown | Other/Unknown |

Use these exact class IDs consistently.

The public class list does not mean all six classes have already
been trained.

3. Photograph Collection Rules

- Collect real field photographs from different physical sites.
- Include different viewing angles, lighting and backgrounds.
- Record the source and licence or permission for each image.
- Use photographs whose intervention type can be verified.
- Record missing information as missing; do not invent it.
- GPS and capture date are useful when available, but missing GPS
  does not prevent image classification.

4. Labelling Rules

- Assign one dominant visible intervention to each training image.
- Verify labels using reliable information about the structure.
- Farm ponds and percolation tanks can look similar.
  Do not guess their function from an ambiguous photograph.
- Keep unclear or mixed scenes aside for review.
- Do not automatically label uncertain examples as Other/Unknown.
- Give photographs of the same physical site the same site_id.

5. Local Storage

| Location inside ai/data/ | Purpose |
|---|---|
| raw/ | Original collected photographs |
| processed/ | Prepared images, when needed |
| manifests/ | Non-sensitive templates and dataset documentation |
| manifests/private/ | Actual records containing private information |

Original photographs should be preserved.

Full datasets and private manifests must remain outside ordinary
Git commits.

6. Dataset Manifest

A manifest is a CSV file with one row per photograph.

Required columns:

image_id,relative_path,class_id,site_id,source,licence_or_permission,capture_date,region,sha256,split

| Column | Meaning |
|---|---|
| image_id | Unique image identifier |
| relative_path | Image path relative to ai/data/ |
| class_id | Verified class ID |
| site_id | Identifier for the physical site or structure |
| source | Where the photograph came from |
| licence_or_permission | Recorded permission or licence |
| capture_date | Capture date, when known |
| region | Geographic region, when known |
| sha256 | File fingerprint for exact-duplicate checking |
| split | train, validation or test after splitting |

Example relative path:
raw/check_dam/photo_001.jpg

Leave split unassigned during initial collection.
The preparation scripts will calculate hashes and assign splits later.

7. Dataset Cleaning

Before training:

- Check that every image can be opened.
- Check that every label is valid and supported by evidence.
- Remove exact duplicates and review near duplicates.
- Group related images, capture sequences and derivative crops.
- Record image counts and distinct site counts for each class.

8. Train, Validation and Test Split

Target approximately:

- Training: 70%
- Validation: 15%
- Test: 15%

Split by site or related-image group.

All photographs of the same structure must stay in one split.
Cropped or edited copies must stay with their original image.

Keeping related images together is more important than achieving
the exact percentages.

Document actual counts and any classes missing from a split.

9. Image Preparation

- Handle image orientation consistently.
- Convert images to RGB.
- Use the preprocessing required by the selected model.
- Apply random augmentation only to training images.
- Use consistent deterministic preprocessing for validation,
  testing and inference.

10. Other/Unknown Behaviour

Train a separate other class only when enough varied, verified
negative examples are available.

Low-confidence predictions should also return Other/Unknown
with human verification required.

Keep the original top candidate separately.

Choose the confidence threshold using validation data.
The example value 0.70 is not a validated threshold.

11. Evaluation Rules

- Use training data to learn model parameters.
- Use validation data to select settings and the threshold.
- Evaluate the frozen model on the held-out test set.
- Report measured results and limitations.
- Do not claim an accuracy value before measuring it.

Track collection progress, completed work and actual validation
results in ai/STATUS.md.