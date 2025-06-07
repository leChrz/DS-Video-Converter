### `convert_for_dsvideo.py`
"""
Adds a stereo AAC fallback track to every audio stream
so Synology DS Video plays MKV/AVI without DTS issues.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

from babelfish import Language
from subliminal import download_best_subtitles, region, save_subtitles, Video

TARGET_LANGS = {Language("deu"), Language("eng")}


def probe_audio(path: Path) -> list[dict]:
    """Return relative index, language and title of each audio stream."""
    raw = subprocess.check_output(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a",
            "-show_entries",
            "stream=index:stream_tags=language,title",
            "-of",
            "json",
            str(path),
        ]
    )
    data = json.loads(raw)["streams"]
    return [
        {
            "rel": i,
            "lang": s.get("tags", {}).get("language", "und"),
            "title": s.get("tags", {}).get("title", ""),
        }
        for i, s in enumerate(data)
    ]


def build_ffmpeg_cmd(src: Path, dst: Path, streams: list[dict]) -> list[str]:
    cmd = ["ffmpeg", "-i", str(src), "-map", "0:v", "-c:v", "copy", "-map", "0:s?", "-c:s", "copy"]

    # 1 prepend AAC clones (become the first audio tracks)
    for s in streams:
        cmd += ["-map", f"0:a:{s['rel']}"]
    for idx, s in enumerate(streams):
        cmd += [
            f"-c:a:{idx}",
            "aac",
            f"-ac:a:{idx}",
            "2",
            f"-b:a:{idx}",
            "160k",
            f"-metadata:s:a:{idx}",
            "title=AAC",
            f"-metadata:s:a:{idx}",
            f"language={s['lang']}",
            f"-disposition:a:{idx}",
            "default",
        ]

    # 2 append untouched originals
    base = len(streams)
    for offset, s in enumerate(streams):
        out_idx = base + offset
        title = s["title"] or "DTS"
        cmd += [
            "-map",
            f"0:a:{s['rel']}",
            f"-c:a:{out_idx}",
            "copy",
            f"-metadata:s:a:{out_idx}",
            f"title={title}",
            f"-metadata:s:a:{out_idx}",
            f"language={s['lang']}",
            f"-disposition:a:{out_idx}",
            "0",
        ]

    cmd.append(str(dst))
    return cmd


def fetch_subs(path: Path):
    region.configure("dogpile.cache.memory")
    video = Video.fromname(path.name)
    subs = download_best_subtitles([video], TARGET_LANGS)
    if subs.get(video):
        save_subtitles(video, subs[video])
        print(f"  ✓ subtitles saved ({path.name})")


def has_external_subs(path: Path) -> bool:
    return any(path.with_suffix("." + ext).exists() for ext in ("srt", "ass", "sub"))


def main():
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found – add it to PATH or install via conda")

    for file in sorted(Path(".").iterdir()):
        if file.suffix.lower() not in {".mkv", ".avi"}:
            continue

        out = file.with_name(f"{file.stem}_DS.mkv")
        if out.exists():
            print(f"⏭  {out.name} already exists")
            continue

        streams = probe_audio(file)
        if not streams:
            print(f"no audio streams in {file.name}")
            continue

        print(f"► converting {file.name}")
        try:
            subprocess.run(build_ffmpeg_cmd(file, out, streams), check=True)
        except subprocess.CalledProcessError as err:
            print(f"ffmpeg failed ({file.name}): {err}")
            continue

        if not has_external_subs(out):
            try:
                fetch_subs(out)
            except Exception as err:
                print(f"  – subtitle download failed: {err}")


if __name__ == "__main__":
    main()
