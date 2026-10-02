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

Current Task
Collect more verified photographs from different physical sites.

Important Files
- ai/config/classes.json
- ai/data/README.md
- ai/.gitignore
- ai/STATUS.md

Validation Results
- Validation date: 2026-10-02.
- Class configuration JSON: loaded and validated successfully.
- Dataset validator: PASS — 7 records.
- Readable images: 7/7.
- Exact duplicate files detected: 0.
- Check Dam: 2 images from 2 recorded sites.
- Farm Pond: 2 images from 2 recorded sites.
- Percolation Tank: 1 image from 1 recorded site.
- Contour Trench: 2 images from 2 recorded sites.
- Other/Unknown examples: 0.
- Pillow version: 12.3.0.
- SHA-256 fields in CSV: 7 blank, allowed during collection.
- Train/validation/test splits: not assigned.
- PyTorch and torchvision versions:- Python version: 3.13.0.
- PyTorch version: 2.14.0.
- torchvision version: 0.29.0.
- PyTorch and torchvision imports: successful.
- Mac GPU (MPS): available.
- Model training and evaluation: not started.
- Image preprocessing: PASS on 2 photographs.
- Preprocessing output: shape (3, 224, 224), float32, CPU.

Next Tasks
1. Create photograph folders for the agreed classes.
2. Create the dataset manifest template.
3. Collect photographs with verified labels and sources.
4. Record image details and physical site identifiers.

Reminder
Update this file after each meaningful work session.
Record actual results rather than planned results.