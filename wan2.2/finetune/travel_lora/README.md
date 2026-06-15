---
license: other
base_model: Wan-AI/Wan2.2-TI2V-5B
tags:
  - wan
  - wan2.2
  - ti2v
  - lora
  - text-image-to-video
  - travel
  - diffsynth
---

# Wan2.2 TI2V 5B Travel LoRA

LoRA weights fine-tuned for `Wan-AI/Wan2.2-TI2V-5B` on a small travel, city, and documentary-style video dataset.

This repository contains only the LoRA weights and reproducibility scripts. You still need the Wan2.2 TI2V 5B base model.

## Files

- `travel_lora_step380.safetensors`: uploaded LoRA checkpoint.
- `scripts/collect_archive_travel_videos.py`: reusable public-domain/CC travel-video collection script.
- `scripts/train_wan22_ti2v_lora_local.sh`: local DiffSynth LoRA training launcher.
- `scripts/infer_wan22_ti2v_lora.py`: DiffSynth inference helper for image + prompt to video.
- `dataset/metadata.csv`: dataset manifest used for the prepared local training set.
- `docs/FINETUNE_RECORD.md`: fine-tuning record.
- `docs/DEPLOYMENT_REPORT.md`: deployment and usage report.

## Quick Use

```bash
huggingface-cli download satoshinji/wan22-ti2v-5b-travel-lora \
  travel_lora_step380.safetensors \
  --local-dir ./models/lora/travel
```

DiffSynth loading:

```python
pipe.load_lora(pipe.dit, "models/lora/travel/travel_lora_step380.safetensors", alpha=0.8)
```

Suggested LoRA strength: start with `alpha=0.6` to `1.0`.

## Example Inference

```bash
python scripts/infer_wan22_ti2v_lora.py \
  --image palace_museum.png \
  --prompt "A cinematic travel documentary view of the Forbidden City, ancient red palace walls and golden roofs, calm daylight, smooth forward camera movement." \
  --lora ./models/lora/travel/travel_lora_step380.safetensors \
  --output outputs/palace_travel_lora.mp4 \
  --size "832*480" \
  --frames 49 \
  --steps 30 \
  --alpha 0.8
```

## Notes

The fine-tuning dataset is small, so this LoRA should be treated as a lightweight travel/documentary-style adapter rather than a broad domain model. For production quality, extend the dataset with more consistent travel footage and captions.
