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
- Implemented single-photograph prediction in ai/inference/predictor.py.
- Passed 14 predictor tests and completed the first photograph prediction.
- Prepared the AI/backend handoff against AI 6fe036e and backend 07a331f.
- Added inference-only package metadata and verified two package isolation tests locally.

Current Task
Hand off the confirmed eight-field AI result and installation files to Person 2. Coordinate database class IDs and nullable threshold handling, then test the complete backend flow.

Important Files
- ai/config/classes.json
- ai/data/README.md
- ai/.gitignore
- ai/STATUS.md
- ai/inference/predictor.py
- ai/inference/contracts.py
- ai/inference/model_loader.py
- ai/inference/BACKEND_HANDOFF.md
- ai/pyproject.toml
- ai/MANIFEST.in
- ai/tests/test_inference_package.py

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
- Predictor tests (2026-10-05): PASS — 14/14.
- Single-photograph prediction (2026-10-05): PASS — completed on CPU.
- Photograph: ai/data/processed/farm_pond/farm_pond_0002.png.
- Photograph split: training.
- Returned class: farm_pond (Farm Pond), matching the recorded label.
- Confidence score: 0.4715189039707184.
- Human verification: required.
- Confidence threshold: unselected.
- Prediction model version: dev-20261005-v1.
- This was a training-photo workflow check; held-out evaluation remains pending.
- Local handoff checks (2026-10-06): PASS — 12 contract, 15 export/loader and 14 predictor tests.
- Local inference package checks (2026-10-06): PASS — 2/2; installed outside the repository without training files or model downloads.
- Package archive checks: no training scripts, datasets, private manifests or saved model weights included.
- Local check environment: Python 3.12.14, PyTorch 2.14.1+cpu, torchvision 0.29.1+cpu, Pillow 12.3.0. These are separate from the Mac results above.
- Actual backend PredictionResponse at 07a331f: four class projections accepted; three internal-only fields rejected. Schema check only.
- Package version: 0.1.0.dev1; separate from model bundle version dev-20261005-v1.
- Installation on Person 2's machine: not yet tested.
- AI installation and handoff files: prepared and verified on Mac.
- Mac verification date: 2026-10-06.
- Installed AI package import: PASS.
- Mac AI test suite: PASS — 43/43.
- Contract tests: 12/12 passed.
- Export and loader tests: 15/15 passed.
- Predictor tests: 14/14 passed.
- Package tests: 2/2 passed.
- Export cleanup test: resolved-path lookup corrected and verified on Mac.

Next Tasks
1. Review and commit the AI-only installation and handoff files on branch ai.
2. Agree the class-ID database lookup and support for threshold=None with Person 2; Person 2 owns backend changes.
3. Share the complete dev-20261005-v1 bundle through the agreed model-file location and check it on Person 2's machine.
4. Test stored photo -> AI result -> prediction persistence -> analysis creation with Person 2.
5. Continue verified photo collection, then train/evaluate a larger dataset and select any confidence threshold using validation data.

Reminder
Update this file after each meaningful work session.
Record actual results rather than planned results.
