#!/usr/bin/env bash
set -euo pipefail

WAN_DIR="${WAN_DIR:-/root/code/Wan2.2/Wan2.2-TI2V-5B}"
DATA_DIR="${DATA_DIR:-data/travel_wikimedia}"
OUT_DIR="${OUT_DIR:-models/train/Wan2.2-TI2V-5B_travel_lora}"
EPOCHS="${EPOCHS:-1}"
REPEAT="${REPEAT:-20}"
LR="${LR:-1e-4}"
RANK="${RANK:-16}"
HEIGHT="${HEIGHT:-480}"
WIDTH="${WIDTH:-832}"
FRAMES="${FRAMES:-49}"

WAN_BASE_DIR="$(dirname "${WAN_DIR}")"
MODEL_ID_WITH_ORIGIN_PATHS="${MODEL_ID_WITH_ORIGIN_PATHS:-Wan-AI/Wan2.2-TI2V-5B:diffusion_pytorch_model*.safetensors}"
MODEL_PATHS="${MODEL_PATHS:-[\"${WAN_DIR}/models_t5_umt5-xxl-enc-bf16.pth\",\"${WAN_DIR}/Wan2.2_VAE.pth\"]}"

PYTHON_BIN="${PYTHON_BIN:-python}"

"${PYTHON_BIN}" -m accelerate.commands.launch examples/wanvideo/model_training/train.py \
  --dataset_base_path "${DATA_DIR}" \
  --dataset_metadata_path "${DATA_DIR}/metadata.csv" \
  --data_file_keys "video" \
  --height "${HEIGHT}" \
  --width "${WIDTH}" \
  --num_frames "${FRAMES}" \
  --dataset_repeat "${REPEAT}" \
  --model_paths "${MODEL_PATHS}" \
  --model_id_with_origin_paths "${MODEL_ID_WITH_ORIGIN_PATHS}" \
  --tokenizer_path "${WAN_DIR}/google/umt5-xxl" \
  --learning_rate "${LR}" \
  --num_epochs "${EPOCHS}" \
  --save_steps 20 \
  --remove_prefix_in_ckpt "pipe.dit." \
  --output_path "${OUT_DIR}" \
  --lora_base_model "dit" \
  --lora_target_modules "q,k,v,o,ffn.0,ffn.2" \
  --lora_rank "${RANK}" \
  --extra_inputs "input_image" \
  --use_gradient_checkpointing \
  --use_gradient_checkpointing_offload \
  --enable_model_cpu_offload
