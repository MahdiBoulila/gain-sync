# Gain Sync

Normalize audio files by EBU R128 loudness and peak levels using bs1770gain and FFmpeg.

## Requirements

Install these before use:

```bash
sudo apt-get install ffmpeg bs1770gain
```

## Usage

```bash
python gain_sync.py --folder /path/to/audio/folder
```

## Features

- Scans folder for `.wav`, `.flac`, `.aiff` files
- Measures EBU R128 loudness with bs1770gain
- Calculates adjustment gains to match reference (median loudness)
- Applies normalization using FFmpeg
- Logs all changes to `changes.log` for inversion

## Inverting Changes

Run with `--invert` to restore original loudness:

```bash
python gain_sync.py --folder /path/to/audio/folder --invert
```
