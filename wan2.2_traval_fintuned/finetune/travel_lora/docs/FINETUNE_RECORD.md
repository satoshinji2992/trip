# Fine-Tuning Record

## Objective

Fine-tune a lightweight LoRA for `Wan-AI/Wan2.2-TI2V-5B` to bias text-image-to-video generation toward travel, city, landmark, and documentary-style footage.

## Base Model

- Base model: `Wan-AI/Wan2.2-TI2V-5B`
- Training framework: DiffSynth-Studio
- Training type: LoRA on DiT modules
- Uploaded checkpoint: `travel_lora_step380.safetensors`

## Dataset

- Prepared local dataset path: `data/travel_archive_30`
- Uploaded manifest: `dataset/metadata.csv`
- Prepared clips: 18 short videos
- Video preprocessing:
  - Resolution: `832x480`
  - FPS: `24`
  - Clip length: about 3 seconds
  - Codec: H.264 mp4
- Source: Internet Archive / Prelinger and reusable public-domain or Creative Commons style archives
- Collection script: `scripts/collect_archive_travel_videos.py`

The raw source downloads were not retained after conversion to avoid unnecessary disk usage.

## Training Configuration

Launcher: `scripts/train_wan22_ti2v_lora_local.sh`

Observed/local settings:

```bash
PYTHON_BIN=/root/anaconda3/envs/wan/bin/python
DIFFSYNTH_MODEL_BASE_PATH=/root/code/Wan2.2
DATA_DIR=data/travel_archive_30
OUT_DIR=models/train/Wan2.2-TI2V-5B_travel_lora
EPOCHS=1
REPEAT=20
RANK=16
FRAMES=49
HEIGHT=480
WIDTH=832
LR=1e-4
```

Core DiffSynth arguments:

```bash
--data_file_keys video
--num_frames 49
--dataset_repeat 20
--learning_rate 1e-4
--save_steps 20
--lora_base_model dit
--lora_target_modules q,k,v,o,ffn.0,ffn.2
--lora_rank 16
--extra_inputs input_image
--use_gradient_checkpointing
--use_gradient_checkpointing_offload
--enable_model_cpu_offload
```

Model loading strategy:

- Diffusion shards were loaded through `Wan-AI/Wan2.2-TI2V-5B:diffusion_pytorch_model*.safetensors`.
- Local T5 and VAE `.pth` files were used to avoid downloading converted common files.
- A local `DIFFSYNTH_MODEL_BASE_PATH` symlink was used so DiffSynth could reuse the existing Wan2.2 model directory.

## Checkpoints

Local training produced periodic checkpoints every 20 steps. The uploaded checkpoint is:

```text
travel_lora_step380.safetensors
```

Local original:

```text
models/train/Wan2.2-TI2V-5B_travel_lora/step-380.safetensors
```

Size: about 77 MiB.

## Known Limitations

- The dataset is intentionally small and should not be treated as a complete travel-video corpus.
- Captions are generated from archive metadata and may be broad.
- The LoRA is best used as a style/domain bias, not as a strong identity or object adapter.
- For higher quality, train on more consistent, manually-captioned clips.

## Reproduction

Collect a dataset:

```bash
python scripts/collect_archive_travel_videos.py \
  --output data/travel_archive_30 \
  --limit 30 \
  --search-limit 800 \
  --seconds 3 \
  --width 832 \
  --height 480 \
  --fps 24
```

Train:

```bash
PYTHON_BIN=/root/anaconda3/envs/wan/bin/python \
DIFFSYNTH_MODEL_BASE_PATH=/root/code/Wan2.2 \
DATA_DIR=data/travel_archive_30 \
OUT_DIR=models/train/Wan2.2-TI2V-5B_travel_lora \
EPOCHS=1 \
REPEAT=20 \
RANK=16 \
FRAMES=49 \
HEIGHT=480 \
WIDTH=832 \
bash scripts/train_wan22_ti2v_lora_local.sh
```
