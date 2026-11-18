# Gain Sync

Normalize audio files by EBU R128 loudness and peak levels using bs1770gain and FFmpeg.

## Requirements

Install these before use:

```bash
sudo apt-get install ffmpeg bs1770gain
```

## Usage

```bash
# Normalize audio files in a folder
python gain_sync.py --folder /path/to/audio/folder

# Invert previous normalizations
python gain_sync.py --folder /path/to/audio/folder --invert
```

## Testing

To test with sample files (requires FFmpeg for conversion):

```bash
cd gain-sync/test_audio

# If you have FFmpeg, convert MP3 to FLAC:
for f in *.mp3; do ffmpeg -i "$f" "${f%.mp3}.flac"; done

# Run gain sync:
python ../gain_sync.py --folder .
```
