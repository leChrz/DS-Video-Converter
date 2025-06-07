## DS Video Friendly Converter

A tiny Python tool that makes any MKV or AVI playable through **Synology Video Station / DS Video** on Fire TV & Co.

### Features
* scans the current folder for `.mkv` / `.avi`
* keeps video and existing subtitles untouched
* **adds a stereo AAC track in front of every original audio track**  
  → DS Video autoselects the first (AAC) track, no more “unsupported DTS” errors
* preserves the original tracks (DTS, AC-3, …) with language & title
* downloads missing German/English subtitles from OpenSubtitles

### Requirements
* Python 3.9+  
  `pip install -r requirements.txt`
* A working `ffmpeg` in your PATH  
  (Windows: `conda install -c conda-forge ffmpeg` is easiest)

### Usage
```bash
conda activate videoconvert      # or any env with the requirements installed
python convert_for_dsvideo.py    # run inside the folder containing your films