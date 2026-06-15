# Deployment Report

## Artifact

- Hugging Face repo: `satoshinji/wan22-ti2v-5b-travel-lora`
- LoRA file: `travel_lora_step380.safetensors`
- Base model required: `Wan-AI/Wan2.2-TI2V-5B`
- Recommended framework: DiffSynth-Studio

## Runtime Environment Used Locally

- Python environment: conda env `wan`
- GPU: NVIDIA GeForce RTX 5090, 32 GiB VRAM
- Torch observed locally: `2.12.0+cu130`
- DiffSynth-Studio installed editable from local clone
- Inference and training used bfloat16 where supported

## Download

```bash
huggingface-cli download satoshinji/wan22-ti2v-5b-travel-lora \
  travel_lora_step380.safetensors \
  --local-dir ./models/lora/travel
```

## DiffSynth Inference

Use `scripts/infer_wan22_ti2v_lora.py`:

```bash
python scripts/infer_wan22_ti2v_lora.py \
  --image input.jpg \
  --prompt "A cinematic travel documentary view of an ancient landmark, smooth camera movement, realistic daylight, detailed architecture." \
  --lora ./models/lora/travel/travel_lora_step380.safetensors \
  --output outputs/travel_lora.mp4 \
  --size "832*480" \
  --frames 49 \
  --steps 30 \
  --alpha 0.8 \
  --seed 1
```

Important parameters:

- `--alpha`: LoRA strength. Try `0.6`, `0.8`, and `1.0`.
- `--steps`: inference steps. `30` is a practical default; `50` may improve quality but is slower.
- `--frames`: `49` is lighter; use more frames only if VRAM and time allow.
- `--size`: `832*480` is the recommended 480p landscape size.

## API Deployment

The previous FastAPI server can support this LoRA by loading it after the Wan/DiffSynth pipeline is created:

```python
pipe.load_lora(pipe.dit, "models/lora/travel/travel_lora_step380.safetensors", alpha=0.8)
```

Recommended API behavior:

- Load the base model and LoRA once on server startup or background preload.
- Keep one generation lock per GPU, because concurrent video generation jobs will otherwise compete for VRAM.
- Accept `image`, `prompt`, `steps`, `frames`, `size`, `seed`, and optional `lora_alpha`.
- Return mp4 output after generation completes.

## Resource Notes

- Base model loading is much larger than the LoRA. The LoRA itself is about 77 MiB.
- First request is slow if the base model is not preloaded.
- CPU offload reduces VRAM pressure but increases latency.
- For 32 GiB VRAM, start with:
  - Size: `832*480`
  - Frames: `49`
  - Steps: `30`
  - LoRA alpha: `0.8`

## Validation

Validated locally:

- DiffSynth model loading with local Wan2.2 base weights
- LoRA checkpoint loading through `pipe.load_lora(pipe.dit, ..., alpha=0.8)`
- Training checkpoint generation up to `step-380.safetensors`
- Hugging Face upload and remote file listing

Remote files expected:

```text
README.md
travel_lora_step380.safetensors
scripts/collect_archive_travel_videos.py
scripts/train_wan22_ti2v_lora_local.sh
scripts/infer_wan22_ti2v_lora.py
dataset/metadata.csv
docs/FINETUNE_RECORD.md
docs/DEPLOYMENT_REPORT.md
```
