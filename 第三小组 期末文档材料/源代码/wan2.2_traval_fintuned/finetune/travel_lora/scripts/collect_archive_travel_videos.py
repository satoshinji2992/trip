#!/usr/bin/env python3
import argparse
import csv
import re
import subprocess
import sys
import time
from pathlib import Path

import requests


ADVANCED_SEARCH = "https://archive.org/advancedsearch.php"
METADATA = "https://archive.org/metadata/{identifier}"
USER_AGENT = "WanTravelLoRACollector/1.0 (local research dataset builder)"
ALLOWED_RIGHTS = ("creativecommons", "creative commons", "public domain", "prelinger")
TRAVEL_TERMS = (
    "travel",
    "tourism",
    "tourist",
    "vacation",
    "journey",
    "trip",
    "scenic",
    "landmark",
    "city",
    "street",
    "architecture",
    "beach",
    "mountain",
    "park",
    "national park",
    "hotel",
    "resort",
    "museum",
    "temple",
    "palace",
)


def get_json(url, params=None, attempts=5):
    last_error = None
    for attempt in range(attempts):
        try:
            response = requests.get(
                url,
                params=params,
                headers={"User-Agent": USER_AGENT},
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            last_error = exc
            time.sleep(2 + attempt * 3)
    raise last_error


def clean(value):
    if value is None:
        return ""
    if isinstance(value, list):
        value = " ".join(str(v) for v in value)
    value = re.sub(r"<[^>]+>", "", str(value))
    return re.sub(r"\s+", " ", value).strip()


def allowed_item(meta):
    haystack = " ".join(
        clean(meta.get(key)).lower()
        for key in ("licenseurl", "rights", "collection", "subject")
    )
    return any(token in haystack for token in ALLOWED_RIGHTS)


def travel_item(meta, doc):
    haystack = " ".join(
        clean(value).lower()
        for value in (
            meta.get("title"),
            meta.get("description"),
            meta.get("subject"),
            doc.get("title"),
            doc.get("description"),
            doc.get("subject"),
        )
    )
    return any(term in haystack for term in TRAVEL_TERMS)


def search_items(query, rows):
    params = {
        "q": query,
        "fl[]": ["identifier", "title", "description", "subject", "licenseurl", "rights", "collection"],
        "sort[]": "downloads desc",
        "rows": str(rows),
        "page": "1",
        "output": "json",
    }
    docs = get_json(ADVANCED_SEARCH, params=params)
    return docs.get("response", {}).get("docs", [])


def choose_video_file(files, max_bytes):
    preferred_formats = ("h.264", "mpeg4", "512kb mpeg4", "matroska", "webm")
    candidates = []
    for item in files:
        name = item.get("name", "")
        fmt = clean(item.get("format")).lower()
        size = int(item.get("size") or 0)
        if not name.lower().endswith((".mp4", ".mov", ".m4v", ".webm", ".ogv", ".mkv")):
            continue
        if size <= 0 or size > max_bytes:
            continue
        score = next((idx for idx, token in enumerate(preferred_formats) if token in fmt), 99)
        candidates.append((score, size, name))
    if not candidates:
        return None
    return sorted(candidates)[0][2]


def download(url, path):
    last_error = None
    for attempt in range(5):
        try:
            with requests.get(
                url,
                headers={"User-Agent": USER_AGENT},
                stream=True,
                timeout=180,
            ) as response:
                response.raise_for_status()
                with open(path, "wb") as out:
                    for chunk in response.iter_content(1024 * 1024):
                        if chunk:
                            out.write(chunk)
            return
        except Exception as exc:
            last_error = exc
            time.sleep(2 + attempt * 3)
    raise last_error


def run(cmd):
    subprocess.run(cmd, check=True)


def convert_video(src, dst, seconds, width, height, fps):
    run([
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-i",
        str(src),
        "-t",
        str(seconds),
        "-vf",
        f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},fps={fps}",
        "-an",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(dst),
    ])


def prompt_for(title, description, subject):
    text = clean(description) or clean(subject) or clean(title)
    text = text[:420]
    return (
        "A cinematic travel documentary video showing "
        f"{text}. Smooth camera movement, realistic daylight, natural colors, "
        "city and landmark travel atmosphere, high detail."
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--query",
        default='collection:prelinger AND mediatype:movies AND (travel OR tourism OR city OR landmark OR scenic)',
    )
    parser.add_argument("--output", default="data/travel_archive")
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument("--search-limit", type=int, default=40)
    parser.add_argument("--max-mb", type=int, default=160)
    parser.add_argument("--seconds", type=float, default=3.0)
    parser.add_argument("--width", type=int, default=832)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--keep-raw", action="store_true")
    args = parser.parse_args()

    output = Path(args.output)
    raw_dir = output / "raw"
    video_dir = output / "videos"
    raw_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    max_bytes = args.max_mb * 1024 * 1024
    for doc in search_items(args.query, args.search_limit):
        if len(rows) >= args.limit:
            break
        identifier = doc.get("identifier")
        if not identifier:
            continue
        metadata = get_json(METADATA.format(identifier=identifier))
        item_meta = metadata.get("metadata", {})
        if not allowed_item(item_meta):
            continue
        if not travel_item(item_meta, doc):
            continue
        video_name = choose_video_file(metadata.get("files", []), max_bytes)
        if not video_name:
            continue

        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", identifier)
        raw_path = raw_dir / Path(video_name).name
        out_name = f"{len(rows):04d}.mp4"
        out_path = video_dir / out_name
        url = f"https://archive.org/download/{identifier}/{video_name}"

        print(f"Downloading {identifier}: {video_name}", flush=True)
        try:
            download(url, raw_path)
            convert_video(raw_path, out_path, args.seconds, args.width, args.height, args.fps)
        except Exception as exc:
            print(f"Skipping {identifier}: {exc}", file=sys.stderr, flush=True)
            continue
        finally:
            if not args.keep_raw and raw_path.exists():
                raw_path.unlink()

        rows.append({
            "video": f"videos/{out_name}",
            "prompt": prompt_for(
                item_meta.get("title") or doc.get("title") or safe,
                item_meta.get("description") or doc.get("description"),
                item_meta.get("subject") or doc.get("subject"),
            ),
            "source_url": f"https://archive.org/details/{identifier}",
            "license": clean(item_meta.get("licenseurl") or item_meta.get("rights") or "Prelinger/public domain collection"),
            "artist": clean(item_meta.get("creator")),
        })
        time.sleep(1)

    metadata_path = output / "metadata.csv"
    with open(metadata_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["video", "prompt", "source_url", "license", "artist"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {metadata_path}")
    if not rows:
        raise SystemExit("No reusable videos were collected. Try a broader query.")


if __name__ == "__main__":
    main()
