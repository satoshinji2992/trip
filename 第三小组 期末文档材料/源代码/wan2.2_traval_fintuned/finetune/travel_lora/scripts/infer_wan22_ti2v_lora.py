#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

import torch
from PIL import Image

from diffsynth.pipelines.wan_video import ModelConfig, WanVideoPipeline
from diffsynth.utils.data import save_video


NEGATIVE_PROMPT = (
    "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，"
    "静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，"
    "多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，"
    "形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，"
    "背景人很多，倒着走"
)


def parse_size(size):
    size = size.lower().replace("x", "*")
    width, height = size.split("*", 1)
    return int(width), int(height)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--output", default="outputs/travel_lora.mp4")
    parser.add_argument("--lora", default="models/train/Wan2.2-TI2V-5B_travel_lora/step-380.safetensors")
    parser.add_argument("--alpha", type=float, default=0.8)
    parser.add_argument("--size", default="832*480")
    parser.add_argument("--frames", type=int, default=49)
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--cfg", type=float, default=5.0)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--fps", type=int, default=15)
    args = parser.parse_args()

    width, height = parse_size(args.size)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("DIFFSYNTH_MODEL_BASE_PATH", "/root/code/Wan2.2")

    pipe = WanVideoPipeline.from_pretrained(
        torch_dtype=torch.bfloat16,
        device="cuda",
        model_configs=[
            ModelConfig(path="/root/code/Wan2.2/Wan2.2-TI2V-5B/models_t5_umt5-xxl-enc-bf16.pth"),
            ModelConfig(model_id="Wan-AI/Wan2.2-TI2V-5B", origin_file_pattern="diffusion_pytorch_model*.safetensors"),
            ModelConfig(path="/root/code/Wan2.2/Wan2.2-TI2V-5B/Wan2.2_VAE.pth"),
        ],
    )
    pipe.load_lora(pipe.dit, args.lora, alpha=args.alpha)

    input_image = Image.open(args.image).convert("RGB").resize((width, height))
    video = pipe(
        prompt=args.prompt,
        negative_prompt=NEGATIVE_PROMPT,
        input_image=input_image,
        height=height,
        width=width,
        num_frames=args.frames,
        num_inference_steps=args.steps,
        cfg_scale=args.cfg,
        seed=args.seed,
        tiled=True,
    )
    save_video(video, args.output, fps=args.fps, quality=5)
    print(args.output)


if __name__ == "__main__":
    main()
