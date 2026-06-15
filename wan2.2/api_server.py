# Copyright 2024-2025 The Alibaba Wan Team Authors. All rights reserved.
import argparse
import asyncio
import logging
import os
import random
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional
from uuid import uuid4

import torch
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from PIL import Image

DIFFSYNTH_ROOT = os.environ.get("DIFFSYNTH_ROOT", "/root/code/DiffSynth-Studio")
if os.path.isdir(DIFFSYNTH_ROOT) and DIFFSYNTH_ROOT not in sys.path:
    sys.path.insert(0, DIFFSYNTH_ROOT)

from diffsynth.pipelines.wan_video import ModelConfig, WanVideoPipeline
from diffsynth.utils.data import save_video


LOGGER = logging.getLogger("wan.api")
TASK = "ti2v-5B"
API_SUPPORTED_SIZES = ("832*480", "480*832", "1280*704", "704*1280")
NEGATIVE_PROMPT = (
    "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，"
    "静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，"
    "多余的手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，"
    "形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，"
    "背景人很多，倒着走"
)


def str2bool(value):
    if isinstance(value, bool):
        return value
    value = value.lower()
    if value in {"yes", "true", "t", "1", "y"}:
        return True
    if value in {"no", "false", "f", "0", "n"}:
        return False
    raise argparse.ArgumentTypeError("boolean value expected")


def parse_size(size: str) -> tuple[int, int]:
    width, height = size.lower().replace("x", "*").split("*", 1)
    return int(width), int(height)
INDEX_HTML = """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Wan2.2 TI2V</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f4f6f8;
      color: #1d252d;
    }
    * { box-sizing: border-box; }
    body { margin: 0; }
    main {
      max-width: 1120px;
      margin: 0 auto;
      padding: 28px 20px 44px;
    }
    header {
      display: flex;
      align-items: end;
      justify-content: space-between;
      gap: 18px;
      margin-bottom: 22px;
      border-bottom: 1px solid #d9e0e7;
      padding-bottom: 18px;
    }
    h1 { margin: 0; font-size: 28px; line-height: 1.2; }
    .status {
      font-size: 13px;
      color: #53616f;
      white-space: nowrap;
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(320px, 420px) 1fr;
      gap: 22px;
      align-items: start;
    }
    form, .preview {
      background: #ffffff;
      border: 1px solid #dbe2e8;
      border-radius: 8px;
      padding: 18px;
      box-shadow: 0 1px 2px rgba(20, 31, 43, 0.05);
    }
    label {
      display: block;
      margin: 0 0 7px;
      font-size: 13px;
      font-weight: 650;
      color: #2f3b46;
    }
    textarea, input, select {
      width: 100%;
      border: 1px solid #c8d2dc;
      border-radius: 6px;
      padding: 10px 11px;
      font: inherit;
      background: #fff;
      color: inherit;
    }
    textarea {
      min-height: 156px;
      resize: vertical;
      line-height: 1.45;
    }
    .field { margin-bottom: 15px; }
    .file-control {
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 10px;
      align-items: center;
    }
    .file-control input {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
    }
    .file-button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 42px;
      border-radius: 6px;
      padding: 0 14px;
      background: #1769e0;
      color: white;
      font-weight: 700;
      cursor: pointer;
      user-select: none;
    }
    .file-name {
      min-width: 0;
      font-size: 13px;
      color: #53616f;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }
    button {
      width: 100%;
      border: 0;
      border-radius: 6px;
      background: #1769e0;
      color: white;
      padding: 12px 14px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }
    button:disabled {
      background: #93a6bd;
      cursor: wait;
    }
    .message {
      min-height: 22px;
      margin-top: 12px;
      font-size: 13px;
      color: #53616f;
      overflow-wrap: anywhere;
    }
    .message.error { color: #b42318; }
    .image-preview {
      display: block;
      width: 100%;
      max-height: 220px;
      object-fit: contain;
      border: 1px solid #dbe2e8;
      border-radius: 6px;
      background: #eef2f5;
      margin-top: 10px;
    }
    video {
      width: 100%;
      aspect-ratio: 1280 / 704;
      background: #111820;
      border-radius: 6px;
      display: block;
    }
    .download {
      display: inline-flex;
      margin-top: 12px;
      color: #1769e0;
      font-weight: 650;
      text-decoration: none;
    }
    @media (max-width: 860px) {
      header { display: block; }
      .status { margin-top: 8px; }
      .layout { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>Wan2.2 TI2V</h1>
      <div class="status" id="health">检查服务状态...</div>
    </header>
    <div class="layout">
      <form id="form">
        <div class="field">
          <label for="image">图片</label>
          <div class="file-control">
            <label class="file-button" for="image">选择图片</label>
            <span id="fileName" class="file-name">未选择文件</span>
            <input id="image" name="image" type="file" accept="image/*" required>
          </div>
          <img id="imagePreview" class="image-preview" alt="" hidden>
        </div>
        <div class="field">
          <label for="prompt">Prompt</label>
          <textarea id="prompt" name="prompt" required>A majestic cinematic travel video of the Forbidden City in Beijing, showcasing ancient Chinese imperial architecture, red walls, golden roofs, stone courtyards, and historical palace details. The camera moves slowly and smoothly like a professional gimbal shot, with warm natural sunlight, subtle atmospheric depth, elegant motion, realistic textures, and a solemn grand cultural mood.</textarea>
        </div>
        <div class="row">
          <div class="field">
            <label for="size">尺寸</label>
            <select id="size" name="size">
              <option value="832*480">832*480 横屏</option>
              <option value="480*832">480*832 竖屏</option>
              <option value="1280*704">1280*704 横屏</option>
              <option value="704*1280">704*1280 竖屏</option>
            </select>
          </div>
          <div class="field">
            <label for="sample_steps">步数</label>
            <input id="sample_steps" name="sample_steps" type="number" min="1" max="100" value="30">
          </div>
        </div>
        <div class="row">
          <div class="field">
            <label for="frame_num">帧数</label>
            <input id="frame_num" name="frame_num" type="number" min="5" step="4" value="49">
          </div>
          <div class="field">
            <label for="seed">Seed</label>
            <input id="seed" name="seed" type="number" value="-1">
          </div>
        </div>
        <button id="submit" type="submit">生成视频</button>
        <div id="message" class="message"></div>
      </form>
      <section class="preview">
        <video id="video" controls hidden></video>
        <div id="empty" class="message">生成完成后会在这里播放视频。</div>
        <a id="download" class="download" download hidden>下载视频</a>
      </section>
    </div>
  </main>
  <script>
    const form = document.getElementById("form");
    const submit = document.getElementById("submit");
    const message = document.getElementById("message");
    const video = document.getElementById("video");
    const download = document.getElementById("download");
    const empty = document.getElementById("empty");
    const image = document.getElementById("image");
    const imagePreview = document.getElementById("imagePreview");
    const fileName = document.getElementById("fileName");
    const health = document.getElementById("health");
    let currentVideoUrl = null;
    let currentImageUrl = null;

    async function updateHealth() {
      try {
        const res = await fetch("/health");
        const data = await res.json();
        const modelState = data.model_loaded ? "已加载" : (data.model_loading ? "加载中" : "未加载");
        const loraState = data.lora_loaded ? "LoRA已加载" : "LoRA未加载";
        health.textContent = `服务正常 · ${data.framework || "Wan"} · ${data.task} · 模型${modelState} · ${loraState}`;
      } catch {
        health.textContent = "服务状态未知";
      }
    }

    image.addEventListener("change", () => {
      if (currentImageUrl) URL.revokeObjectURL(currentImageUrl);
      const file = image.files[0];
      if (!file) {
        fileName.textContent = "未选择文件";
        imagePreview.hidden = true;
        return;
      }
      fileName.textContent = file.name;
      currentImageUrl = URL.createObjectURL(file);
      imagePreview.src = currentImageUrl;
      imagePreview.hidden = false;
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      message.className = "message";
      message.textContent = "生成中，请保持页面打开...";
      submit.disabled = true;
      submit.textContent = "生成中";
      video.hidden = true;
      download.hidden = true;
      empty.hidden = false;

      if (currentVideoUrl) URL.revokeObjectURL(currentVideoUrl);

      const body = new FormData(form);
      try {
        const res = await fetch("/generate", { method: "POST", body });
        if (!res.ok) {
          let detail = await res.text();
          try { detail = JSON.parse(detail).detail || detail; } catch {}
          throw new Error(detail);
        }
        const blob = await res.blob();
        currentVideoUrl = URL.createObjectURL(blob);
        video.src = currentVideoUrl;
        video.hidden = false;
        empty.hidden = true;
        download.href = currentVideoUrl;
        download.download = res.headers.get("X-Video-Path")?.split("/").pop() || "wan-video.mp4";
        download.hidden = false;
        message.textContent = "生成完成。";
        updateHealth();
      } catch (error) {
        message.className = "message error";
        message.textContent = `生成失败：${error.message}`;
      } finally {
        submit.disabled = false;
        submit.textContent = "生成视频";
      }
    });

    updateHealth();
    setInterval(updateHealth, 5000);
  </script>
</body>
</html>
"""


class WanApiState:

    def __init__(self, args):
        self.args = args
        self.pipeline = None
        self.loading = False
        self.load_error = None
        self.lora_loaded = False
        self.lora_path = None
        self.lock = asyncio.Lock()

    def resolve_lora_path(self):
        if not self.args.lora_path:
            return None
        candidates = [
            Path(self.args.lora_path),
            Path("/root/code/DiffSynth-Studio/models/train/Wan2.2-TI2V-5B_travel_lora/step-380.safetensors"),
        ]
        for path in candidates:
            if path.exists():
                return path
        return candidates[0]

    def load_pipeline(self):
        if self.pipeline is not None:
            return self.pipeline

        LOGGER.info("Loading DiffSynth WanVideoPipeline from %s", self.args.ckpt_dir)
        self.loading = True
        self.load_error = None
        try:
            if torch.cuda.is_available():
                torch.cuda.set_device(self.args.device_id)
                device = f"cuda:{self.args.device_id}"
            else:
                device = "cpu"

            os.environ.setdefault(
                "DIFFSYNTH_MODEL_BASE_PATH",
                str(Path(self.args.ckpt_dir).resolve().parent),
            )

            self.pipeline = WanVideoPipeline.from_pretrained(
                torch_dtype=torch.bfloat16,
                device=device,
                model_configs=[
                    ModelConfig(path=str(Path(self.args.ckpt_dir) / "models_t5_umt5-xxl-enc-bf16.pth")),
                    ModelConfig(
                        model_id="Wan-AI/Wan2.2-TI2V-5B",
                        origin_file_pattern="diffusion_pytorch_model*.safetensors",
                    ),
                    ModelConfig(path=str(Path(self.args.ckpt_dir) / "Wan2.2_VAE.pth")),
                ],
            )
            lora_path = self.resolve_lora_path()
            if lora_path is not None:
                if not lora_path.exists():
                    raise FileNotFoundError(f"LoRA file not found: {lora_path}")
                self.pipeline.load_lora(
                    self.pipeline.dit,
                    str(lora_path),
                    alpha=self.args.lora_alpha,
                )
                self.lora_loaded = True
                self.lora_path = str(lora_path)
                LOGGER.info("Loaded LoRA %s with alpha=%s", lora_path, self.args.lora_alpha)
        except Exception as exc:
            self.load_error = str(exc)
            raise
        finally:
            self.loading = False
        LOGGER.info("DiffSynth WanVideoPipeline loaded")
        return self.pipeline

    def generate_video(
        self,
        prompt: str,
        image: Image.Image,
        size: str,
        frame_num: Optional[int],
        sample_steps: Optional[int],
        sample_shift: Optional[float],
        sample_guide_scale: Optional[float],
        sample_solver: str,
        seed: int,
        offload_model: bool,
    ) -> Path:
        pipeline = self.load_pipeline()

        width, height = parse_size(size)
        frame_num = frame_num if frame_num is not None else self.args.frame_num
        sample_steps = (
            sample_steps if sample_steps is not None else self.args.sample_steps)
        sample_shift = sample_shift if sample_shift is not None else self.args.sample_shift
        sample_guide_scale = (
            sample_guide_scale if sample_guide_scale is not None else self.args.sample_guide_scale)
        seed = seed if seed >= 0 else random.randint(0, sys.maxsize)

        LOGGER.info(
            "Generating video with DiffSynth: size=%s frame_num=%s steps=%s cfg=%s seed=%s lora=%s prompt=%r",
            size, frame_num, sample_steps, sample_guide_scale, seed, self.lora_path, prompt)

        video = pipeline(
            prompt=prompt,
            negative_prompt=NEGATIVE_PROMPT,
            input_image=image.resize((width, height)),
            height=height,
            width=width,
            num_frames=frame_num,
            num_inference_steps=sample_steps,
            sigma_shift=sample_shift,
            cfg_scale=sample_guide_scale,
            seed=seed,
            tiled=True,
        )

        output_dir = Path(self.args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"ti2v_{size.replace('*', 'x')}_{timestamp}_{uuid4().hex[:8]}.mp4"

        save_video(video, str(output_path), fps=self.args.fps, quality=5)

        del video
        if torch.cuda.is_available():
            torch.cuda.synchronize()
            torch.cuda.empty_cache()

        if not output_path.exists():
            raise RuntimeError("Video saving failed")

        LOGGER.info("Video saved to %s", output_path)
        return output_path


def parse_args():
    parser = argparse.ArgumentParser(
        description="Serve Wan TI2V generation over HTTP.")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Bind address. Use 0.0.0.0 for LAN access.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--ckpt_dir",
        default="./Wan2.2-TI2V-5B",
        help="Path to Wan2.2-TI2V-5B checkpoint directory.")
    parser.add_argument(
        "--output_dir",
        default="./api_outputs",
        help="Directory for generated mp4 files.")
    parser.add_argument(
        "--size",
        default="832*480",
        choices=API_SUPPORTED_SIZES,
        help="Default output size.")
    parser.add_argument(
        "--sample_steps",
        type=int,
        default=30,
        help="Default sampling steps for requests.")
    parser.add_argument(
        "--frame_num",
        type=int,
        default=49,
        help="Default number of frames. Must be 4n+1.")
    parser.add_argument(
        "--sample_shift",
        type=float,
        default=5.0,
        help="Default scheduler sigma shift.")
    parser.add_argument(
        "--sample_guide_scale",
        type=float,
        default=5.0,
        help="Default classifier-free guidance scale.")
    parser.add_argument(
        "--fps",
        type=int,
        default=15,
        help="Output video fps.")
    parser.add_argument(
        "--lora_path",
        default="./finetune/travel_lora/weights/travel_lora_step380.safetensors",
        help="Optional DiffSynth LoRA path. If missing, falls back to the local training output when present.")
    parser.add_argument(
        "--lora_alpha",
        type=float,
        default=0.8,
        help="LoRA strength for DiffSynth load_lora.")
    parser.add_argument("--device_id", type=int, default=0)
    parser.add_argument("--t5_cpu", action="store_true", default=False)
    parser.add_argument(
        "--convert_model_dtype", action="store_true", default=False)
    parser.add_argument(
        "--offload_model",
        type=str2bool,
        default=True,
        help="Default offload_model value for requests.")
    parser.add_argument(
        "--load_on_start",
        action="store_true",
        default=False,
        help="Load the model during API startup instead of on the first request.")
    return parser.parse_args()


def create_app(args):
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        handlers=[logging.StreamHandler(stream=sys.stdout)])

    if not os.path.isdir(args.ckpt_dir):
        raise FileNotFoundError(f"Checkpoint directory not found: {args.ckpt_dir}")

    state = WanApiState(args)
    app = FastAPI(title="Wan2.2 TI2V API", version="1.0")

    @app.on_event("startup")
    async def load_model_on_startup():
        if not args.load_on_start:
            return

        async def background_load():
            async with state.lock:
                try:
                    await asyncio.to_thread(state.load_pipeline)
                except Exception:
                    LOGGER.exception("Model preload failed")

        asyncio.create_task(background_load())

    @app.get("/", response_class=HTMLResponse)
    def index():
        return INDEX_HTML

    @app.get("/favicon.ico")
    def favicon():
        return HTMLResponse(status_code=204)

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "task": TASK,
            "framework": "DiffSynth",
            "model_loaded": state.pipeline is not None,
            "model_loading": state.loading,
            "load_error": state.load_error,
            "default_size": args.size,
            "default_frame_num": args.frame_num,
            "lora_loaded": state.lora_loaded,
            "lora_path": state.lora_path,
            "lora_alpha": args.lora_alpha,
        }

    @app.post("/generate")
    async def generate(
        prompt: str = Form(...),
        image: UploadFile = File(...),
        size: str = Form(None),
        frame_num: Optional[int] = Form(None),
        sample_steps: Optional[int] = Form(None),
        sample_shift: Optional[float] = Form(None),
        sample_guide_scale: Optional[float] = Form(None),
        sample_solver: str = Form("unipc"),
        seed: int = Form(-1),
        offload_model: Optional[bool] = Form(None),
    ):
        size = size or args.size
        offload_model = args.offload_model if offload_model is None else offload_model

        if not prompt.strip():
            raise HTTPException(status_code=400, detail="prompt cannot be empty")
        if size not in API_SUPPORTED_SIZES:
            raise HTTPException(
                status_code=400,
                detail=f"unsupported size {size}; supported: {API_SUPPORTED_SIZES}")
        if sample_solver not in {"unipc", "dpm++"}:
            raise HTTPException(
                status_code=400, detail="sample_solver must be unipc or dpm++")
        if frame_num is not None and (frame_num - 1) % 4 != 0:
            raise HTTPException(
                status_code=400, detail="frame_num must be 4n+1")

        try:
            image_bytes = await image.read()
            pil_image = Image.open(BytesIO(image_bytes)).convert("RGB")
        except Exception as exc:
            raise HTTPException(
                status_code=400, detail=f"invalid image: {exc}") from exc

        async with state.lock:
            try:
                output_path = await asyncio.to_thread(
                    state.generate_video,
                    prompt.strip(),
                    pil_image,
                    size,
                    frame_num,
                    sample_steps,
                    sample_shift,
                    sample_guide_scale,
                    sample_solver,
                    seed,
                    offload_model,
                )
            except Exception as exc:
                LOGGER.exception("Generation failed")
                raise HTTPException(
                    status_code=500, detail=f"generation failed: {exc}") from exc

        return FileResponse(
            path=str(output_path),
            media_type="video/mp4",
            filename=output_path.name,
            headers={"X-Video-Path": str(output_path)})

    return app


args = parse_args()
app = create_app(args)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port)
