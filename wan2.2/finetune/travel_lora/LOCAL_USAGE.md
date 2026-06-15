# Local Usage In `/root/code/Wan2.2`

This folder stores the travel LoRA fine-tuning code, records, and deployment notes for the local Wan2.2 project.

The actual DiffSynth training framework is located at:

```text
/root/code/DiffSynth-Studio
```

The uploaded LoRA checkpoint is available at:

```text
https://huggingface.co/satoshinji/wan22-ti2v-5b-travel-lora
```

## Files

```text
README.md
scripts/collect_archive_travel_videos.py
scripts/train_wan22_ti2v_lora_local.sh
scripts/infer_wan22_ti2v_lora.py
dataset/metadata.csv
docs/FINETUNE_RECORD.md
docs/DEPLOYMENT_REPORT.md
```

## Train From Wan2.2 Project

```bash
cd /root/code/DiffSynth-Studio

PYTHON_BIN=/root/anaconda3/envs/wan/bin/python \
DIFFSYNTH_MODEL_BASE_PATH=/root/code/Wan2.2 \
WAN_DIR=/root/code/Wan2.2/Wan2.2-TI2V-5B \
DATA_DIR=/root/code/DiffSynth-Studio/data/travel_archive_30 \
OUT_DIR=/root/code/DiffSynth-Studio/models/train/Wan2.2-TI2V-5B_travel_lora \
EPOCHS=1 \
REPEAT=20 \
RANK=16 \
FRAMES=49 \
HEIGHT=480 \
WIDTH=832 \
bash /root/code/Wan2.2/finetune/travel_lora/scripts/train_wan22_ti2v_lora_local.sh
```

## Download LoRA

```bash
cd /root/code/Wan2.2

huggingface-cli download satoshinji/wan22-ti2v-5b-travel-lora \
  travel_lora_step380.safetensors \
  --local-dir finetune/travel_lora/weights
```

## Inference

Run from DiffSynth-Studio so the `diffsynth` package and examples are available:

```bash
cd /root/code/DiffSynth-Studio

/root/anaconda3/envs/wan/bin/python /root/code/Wan2.2/finetune/travel_lora/scripts/infer_wan22_ti2v_lora.py \
  --image /root/code/Wan2.2/palace_museum.png \
  --prompt "A cinematic travel documentary view of the Forbidden City, ancient red palace walls and golden roofs, calm daylight, smooth forward camera movement." \
  --lora /root/code/Wan2.2/finetune/travel_lora/weights/travel_lora_step380.safetensors \
  --output /root/code/Wan2.2/api_outputs/palace_travel_lora.mp4 \
  --size "832*480" \
  --frames 49 \
  --steps 30 \
  --alpha 0.8
```

## Start The DiffSynth API

`/root/code/Wan2.2/api_server.py` has been switched to DiffSynth `WanVideoPipeline`.

From `/root/code/Wan2.2`:

```bash
/root/anaconda3/envs/wan/bin/python api_server.py \
  --host 0.0.0.0 \
  --port 8000 \
  --ckpt_dir ./Wan2.2-TI2V-5B \
  --sample_steps 30 \
  --frame_num 49 \
  --lora_path ./finetune/travel_lora/weights/travel_lora_step380.safetensors \
  --lora_alpha 0.8 \
  --load_on_start
```

If `--lora_path` does not exist locally, the API falls back to:

```text
/root/code/DiffSynth-Studio/models/train/Wan2.2-TI2V-5B_travel_lora/step-380.safetensors
```

Check status:

```bash
curl http://127.0.0.1:8000/health
```
