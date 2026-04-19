---
title: DeepFake Detect
emoji: 🎭
colorFrom: red
colorTo: gray
sdk: docker
app_port: 7860
short_description: Face-level deepfake video detection with a Docker-based web app.
---

# DeepFake-Detect

A Python-based deepfake video detection project with two main parts:

1. An offline training pipeline that extracts frames, crops faces, prepares labeled data, and trains a binary classifier.
2. A Flask web application that accepts uploaded videos, analyzes faces, returns authenticity scores, and generates a processed preview video with face boxes.

The current repository is focused on face-level deepfake detection rather than general-purpose video understanding.

## What This Project Does

- Takes videos as input and samples frames once per second.
- Uses `MTCNN` to detect and crop faces from extracted frames.
- Uses FaceForensics++ CSV metadata to label face samples as `REAL` or `FAKE`.
- Filters out very small face crops and builds `train / val / test` datasets.
- Trains an `EfficientNetB0`-based classifier with transfer learning and fine-tuning.
- Provides a Flask web app for interactive video analysis.

## Tech Stack

- Backend: `Flask`
- Deep learning: `TensorFlow / Keras`
- Main classifier: `EfficientNetB0`
- Face detection for training/inference crops: `MTCNN`
- Face detection for preview overlays: `YOLOv8 face`
- Video processing: `OpenCV`, `ffmpeg` via `imageio-ffmpeg`
- Dataset splitting: `split-folders`

## Detection Pipeline

### Training Stage

#### 1. Convert videos to frames
Script: [00-convert_video_to_image.py](/Users/zhangke/Documents/Projects/DeepFake-Detect/00-convert_video_to_image.py)

- Reads videos from subfolders under `train_sample_videos/FaceForensics++_C23/`.
- Extracts 1 frame per second.
- Dynamically rescales each frame based on source resolution:
  - Width `< 300`: scale to `2x`
  - Width `> 1900`: scale to `0.33x`
  - Width `1000 ~ 1900`: scale to `0.5x`
  - Otherwise: keep original size
- Stores extracted PNG frames in a per-video directory.

#### 2. Detect and crop faces
Script: [01-crop_faces_with_mtcnn.py](/Users/zhangke/Documents/Projects/DeepFake-Detect/01-crop_faces_with_mtcnn.py)

- Runs `MTCNN` on every extracted frame.
- If a frame contains only one face, that detection is kept.
- If a frame contains multiple faces, only detections with confidence above `0.95` are kept.
- Expands each bounding box by `30%` to preserve more facial context.
- Saves cropped faces into a `faces/` subdirectory for each video.

#### 3. Prepare the dataset
Script: [02-prepare_fake_real_dataset.py](/Users/zhangke/Documents/Projects/DeepFake-Detect/02-prepare_fake_real_dataset.py)

- Reads labels from `csv/*.csv`.
- Copies face crops into:
  - `prepared_dataset/real`
  - `prepared_dataset/fake`
- Filters out any image with width or height smaller than `90px`.
- Splits the final dataset with `split-folders` into:
  - `split_dataset/train`
  - `split_dataset/val`
  - `split_dataset/test`

#### 4. Train the classifier
Script: [03-train_cnn.py](/Users/zhangke/Documents/Projects/DeepFake-Detect/03-train_cnn.py)

- Input size: `224x224`
- Backbone: `EfficientNetB0(weights="imagenet")`
- Output: single-unit `sigmoid` binary classifier
- Training strategy:
  - Phase 1: freeze the backbone and train only the head with learning rate `1e-3`
  - Phase 2: unfreeze the full model and fine-tune with learning rate `1e-5`
- Data augmentation includes:
  - rotation
  - horizontal flip
  - zoom
  - translation
  - brightness jitter
- Uses:
  - `EarlyStopping`
  - `ModelCheckpoint`
  - `ReduceLROnPlateau`
- Applies class weights to reduce `fake/real` imbalance.

The best trained model is saved to:

```text
tmp_checkpoint/best_model.keras
```

This is the canonical model output path used by the training pipeline.

## Web App Inference Flow

App entry point: [App/app.py](/Users/zhangke/Documents/Projects/DeepFake-Detect/App/app.py)

Routes: [App/route.py](/Users/zhangke/Documents/Projects/DeepFake-Detect/App/route.py)

Frontend files:

- [App/templates/index.html](/Users/zhangke/Documents/Projects/DeepFake-Detect/App/templates/index.html)
- [App/static/app.jsx](/Users/zhangke/Documents/Projects/DeepFake-Detect/App/static/app.jsx)
- [App/static/Product.jsx](/Users/zhangke/Documents/Projects/DeepFake-Detect/App/static/Product.jsx)
- [App/static/Technology.jsx](/Users/zhangke/Documents/Projects/DeepFake-Detect/App/static/Technology.jsx)

### Actual inference logic

When a video is uploaded, the backend performs these steps:

1. Validates the file type: `mp4`, `avi`, `mov`, `mkv`, `wmv`
2. Re-encodes the uploaded video to browser-friendly `H.264`
3. Reads frames roughly once per second
4. Uses `MTCNN` to extract faces for classification
5. Runs `EfficientNetB0` inference on each face crop
6. Sorts all face scores from highest to lowest and averages the top `30%`
7. If the averaged score is `> 0.5`, the video is labeled `REAL`; otherwise `FAKE`
8. Returns:
   - final label
   - confidence
   - model score
   - number of faces analyzed
   - face thumbnails with per-face scores
9. Uses `YOLOv8 face` to generate a preview video with face bounding boxes

Notes:

- `MTCNN` is used for the actual face crops fed into the classifier.
- `YOLOv8 face` is currently used for visualization in the processed preview video, not as the classifier itself.

## Repository Structure

```text
DeepFake-Detect/
├── 00-convert_video_to_image.py
├── 01-crop_faces_with_mtcnn.py
├── 02-prepare_fake_real_dataset.py
├── 03-train_cnn.py
├── tmp_checkpoint/
│   ├── best_model.keras
│   └── best_model_phase1.keras
├── App/
│   ├── app.py
│   ├── route.py
│   ├── yolov8n-face.pt
│   ├── static/
│   └── templates/
├── train_sample_videos/
│   └── FaceForensics++_C23/
├── best_model.keras
├── pyproject.toml
└── uv.lock
```

## Dataset Layout

The training scripts expect the dataset root at:

```text
train_sample_videos/FaceForensics++_C23/
```

The repository currently contains these visible subdirectories:

- `original`
- `Deepfakes`
- `DeepFakeDetection`
- `Face2Face`
- `FaceSwap`
- `FaceShifter`
- `NeuralTextures`
- `csv`

CSV files include fields such as:

- `File Path`
- `Label`
- `Frame Count`
- `Width`
- `Height`
- `Codec`
- `File Size(MB)`

## Requirements

- Python `>= 3.12`
- `uv` is recommended
- For training, an NVIDIA GPU that TensorFlow can detect is strongly recommended
- For the web app, a working `ffmpeg` runtime is required; the project accesses it through `imageio-ffmpeg`

## Install Dependencies

### Option 1: use uv

```bash
uv sync
```

### Option 2: use venv + pip

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Quick Start

### 1. Prepare the model file

The web app resolves the model in this order:

```text
tmp_checkpoint/best_model.keras
best_model.keras
```

`tmp_checkpoint/best_model.keras` is the canonical location. The root-level `best_model.keras` is treated as a compatibility fallback only.

If you want the project to use the standard training output path, place the model here:

```bash
mkdir -p tmp_checkpoint
cp best_model.keras tmp_checkpoint/best_model.keras
```

If you want to train from scratch, follow the training sequence below. The training script will generate this file automatically.

### 2. Start the web app

```bash
uv run python App/app.py
```

Then open:

```text
http://127.0.0.1:5001
```

The app now defaults to port `5001`. You can override it with an environment variable:

```bash
PORT=5050 uv run python App/app.py
```

## Hugging Face Spaces Deployment

This repository is now prepared for a Docker-based Hugging Face Space.

Deployment files:

- [Dockerfile](/Users/zhangke/Documents/Projects/DeepFake-Detect/Dockerfile)
- [.dockerignore](/Users/zhangke/Documents/Projects/DeepFake-Detect/.dockerignore)
- [requirements.txt](/Users/zhangke/Documents/Projects/DeepFake-Detect/requirements.txt)

The Space configuration is defined in the YAML header at the top of this README:

- `sdk: docker`
- `app_port: 7860`

Container runtime behavior:

- The container runs the Flask app with `python App/app.py`
- The Docker image sets `PORT=7860`
- The Docker image sets `ENABLE_PREVIEW_FACE_DETECTOR=0`
- The app itself already supports `PORT`, so it matches Hugging Face Spaces routing

Recommended deployment steps:

1. Create a new Hugging Face Space and choose `Docker` as the SDK.
2. Push this repository to that Space repository.
3. Wait for the image build to complete.
4. Open the Space once the container becomes healthy.

Notes for this project on Spaces:

- The Docker build excludes local training data and the duplicate root-level `best_model.keras` from the build context.
- The canonical runtime model remains `tmp_checkpoint/best_model.keras`.
- The app uses CPU by default unless you assign GPU hardware to the Space.
- To keep the Docker image smaller and easier to build, the Space disables YOLO-based preview overlays by default and falls back to a re-encoded original video.

Local Docker smoke test:

```bash
docker build -t deepfake-detect-space .
docker run --rm -p 7860:7860 deepfake-detect-space
```

Then open:

```text
http://127.0.0.1:7860
```

## Training Order

To reproduce the full training pipeline, run the scripts in this order:

```bash
uv run python 00-convert_video_to_image.py
uv run python 01-crop_faces_with_mtcnn.py
uv run python 02-prepare_fake_real_dataset.py
uv run python 03-train_cnn.py
```

## Key Outputs

- Frame extraction output: per-video frame folders
- Face crops: `faces/` inside each processed video folder
- Aggregated dataset: `prepared_dataset/`
- Train/validation/test splits: `split_dataset/`
- Trained model: `tmp_checkpoint/best_model.keras`
- Phase 1 checkpoint: `tmp_checkpoint/best_model_phase1.keras`
- Compatibility fallback model: `best_model.keras`
- Web upload directory: `App/uploads/`
- Inference diagnostics log: `App/diag_log.txt`

## Important Implementation Details

These details matter when understanding the current system:

- This is a face-crop-based binary classifier, not an end-to-end video transformer.
- The model score semantics are: values closer to `1` mean more likely real, values closer to `0` mean more likely fake.
- The video-level decision is not a plain average across all faces; it uses the mean of the highest-scoring subset.
- The upload endpoint enforces a `200 MB` limit.
- The app cleans old uploaded files, so `App/uploads/` should not be treated as persistent storage.

## Known Limitations

- Both training and inference depend heavily on face detection quality.
- The current sampling strategy uses only 1 frame per second, which may miss short-lived manipulation artifacts.
- The repository does not currently provide a standalone CLI inference script; the primary entry point is the Flask app.
- The canonical model path is `tmp_checkpoint/best_model.keras`, but the app also supports `best_model.keras` in the repository root as a fallback.
- This README is based on the current codebase behavior. If UI text and code behavior differ, trust the code.

## Possible Next Improvements

- Add a CLI inference entry point
- Move paths, thresholds, and input/output directories into configuration
- Persist training metrics and experiment logs
- Add batch video inference support
- Add Docker and deployment documentation

## License

No explicit license file is present in the repository at the moment. If you plan to publish or use this project commercially, add a proper license first.
