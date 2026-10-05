AI Module Status

Owner
Person 3 — AI Image Classification

Working Branch
ai

Completed
- Prepared class IDs and labels in ai/config/classes.json.
- Prepared the photograph dataset guide in ai/data/README.md.
- Added ignore rules in ai/.gitignore.
- Updated the AI scope to four intervention classes plus Other/Unknown.
- Removed plantation from the class configuration and dataset guide.
- Created ai/training/validate_dataset.py.
- Added seven sample photographs and their private manifest records.
- Converted the second farm-pond MPO image into a single-frame RGB PNG while preserving the original file.
- Verified PyTorch and torchvision imports and confirmed Mac GPU availability.
- Added image preprocessing in ai/inference/preprocess.py.
- Implemented the CSV-based dataset loader in ai/training/dataset.py.
- Successfully checked photograph loading and PyTorch batching.
- Expanded the photograph collection to 8 images, with 2 images in each of the four intervention classes.
- Implemented ai/training/hash_manifest.py with preview and CSV backup support.
- Recorded and validated SHA-256 fingerprints for all 12 photographs.
- Successfully loaded all 12 photographs through the dataset loader.
- Added ai/inference/model.py as the shared MobileNetV2 model structure.
- Added check_dam_0004 and farm_pond_0004 with source and licence details.
- Prepared ai/config/train.yaml with initial training settings.
- Implemented site-grouped split preparation and added automated tests.
- Saved a development split and verified all three dataset loaders.
- Implemented the development training script and completed the first 10-epoch training run.
- Saved the best development checkpoint using validation macro F1.
- Implemented the AI prediction result contract in ai/inference/contracts.py.
- Added and successfully ran 12 prediction contract tests.
- Implemented the development model exporter and CPU model loader.
- Created development bundle dev-20261005-v1 and verified CPU loading.

Current Task
Implement ai/inference/predictor.py to classify one photograph using the exported development bundle and return the agreed PredictionResult.

Important Files
- ai/config/classes.json
- ai/data/README.md
- ai/.gitignore
- ai/STATUS.md

Validation Results
- Latest dataset validation date: 2026-10-04.
- Class configuration JSON: loaded and validated successfully.
- Dataset validator: PASS — 15 records.
- Readable images: 15/15.
- Exact duplicate files detected: 0.
- Check Dam: 4 images from 4 recorded sites.
- Farm Pond: 4 images from 4 recorded sites.
- Percolation Tank: 3 images from 3 recorded sites.
- Contour Trench: 4 images from 3 recorded sites.
- Other/Unknown examples: 0.
- SHA-256 fields: 15 populated, 0 blank; all match their image files.
- Development split: 7 training, 4 validation, 4 test photographs.
- Distinct site groups: 13.
- Unassigned splits: 0.
- Python version: 3.13.0.
- Pillow version: 12.3.0.
- PyTorch version: 2.14.0.
- torchvision version: 0.29.0.
- PyTorch and torchvision imports: successful.
- Mac GPU (MPS): available.
- Earlier standalone preprocessing check: PASS on 2 photographs.
- Preprocessing output: shape (3, 224, 224), float32, CPU.
- Earlier collection loader check (2026-10-03): PASS — 15/15 photographs loaded with labels from the manifest.
- Training dataset loader check (2026-10-04): PASS — 7/7.
- Validation dataset loader check (2026-10-04): PASS — 4/4.
- Test dataset loader check (2026-10-04): PASS — 4/4; loading check only.
- Class mapping: consistent across all three splits.
- First batch: images (4, 3, 224, 224), labels (4,).
- Model structure check (2026-10-03): PASS on CPU using random weights.
- Model input shapes: (1, 3, 224, 224) and (4, 3, 224, 224).
- Model output shapes: (1, 4) and (4, 4).
- Classification-head gradients and frozen-backbone checks: PASS.
- Backbone unfreeze and evaluation-mode checks: PASS.
- Training preflight check (2026-10-04): PASS.
- Pretrained MobileNetV2 V2 weights: downloaded successfully.
- First development training date: 2026-10-04.
- Development training: PASS — 10 epochs completed.
- Training photographs: 7.
- Validation photographs: 4.
- Best checkpoint: epoch 7.
- Best validation macro F1: 0.2500.
- Validation loss at the selected epoch: 1.3960.
- Checkpoint: ai/models/training_runs/dev-20261004T094431Z-bns0tl6u/best.pt.
- Held-out test evaluation: not performed.
- Confidence threshold: not selected.
- Development result only; the dataset is too small for reliable accuracy claims.
- AI prediction contract tests (2026-10-05): PASS — 12/12.
- Contract checks covered class labels, confidence values, review rules, fallback behaviour and JSON serialization.
- Full backend integration: not yet tested.
- Export preflight (2026-10-05): PASS on the epoch-7 checkpoint.
- Bundle integrity and CPU loading (2026-10-05): PASS.
- Bundle version: dev-20261005-v1.
- Bundle location: ai/models/bundles/dev-20261005-v1/.
- Loaded model output shape: (1, 4), CPU.
- Bundle confidence threshold: unselected; human review required.
- Photograph prediction check: not yet performed.

Next Tasks
1. Create photograph folders for the agreed classes.
2. Create the dataset manifest template.
3. Collect photographs with verified labels and sources.
4. Record image details and physical site identifiers.

Reminder
Update this file after each meaningful work session.
Record actual results rather than planned results.