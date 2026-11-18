# Gain Sync

Normalize audio files by EBU R128 loudness and peak levels using bs1770gain and FFmpeg.

## Requirements

Install these before use:

**Linux/macOS:**
```bash
sudo apt-get install ffmpeg bs1770gain  # Ubuntu/Debian
# or
brew install ffmpeg bs1770gain          # macOS
```

**Windows:**
1. Download and install [FFmpeg](https://ffmpeg.org/download.html)
2. Download and install [bs1770gain](https://github.com/Mayou31/bs1770gain/releases)

## Usage

```bash
# Normalize audio files in a folder
python gain_sync.py --folder /path/to/audio/folder

# Invert previous normalizations
python gain_sync.py --folder /path/to/audio/folder --invert
```

## Features

- Scans folder for `.wav`, `.flac`, `.aiff`, `.mp3` files
- Measures EBU R128 loudness with bs1770gain or FFmpeg
- Calculates adjustment gains to match reference (median loudness)
- Applies normalization using FFmpeg
- Preserves original file extension (MP3 stays MP3, FLAC stays FLAC)
- Logs all changes to `changes.log` for inversion

## Inverting Changes

Run with `--invert` to restore original loudness:

```bash
python gain_sync.py --folder /path/to/audio/folder --invert
```

This reads the `changes.log` file and applies the inverse gain to each file.

## How It Works

1. **Measurement**: Uses bs1770gain or FFmpeg's ebur128 filter to measure loudness
2. **Calculation**: Calculates gain needed to reach -14 LUFS (standard target)
3. **Normalization**: Applies gain via FFmpeg's `volume` filter
4. **Logging**: Records original loudness and adjustment for potential revert

## Quality Considerations

- **Lossless formats (FLAC, AIFF, WAV)**: Effectively lossless - audio data unchanged
- **Lossy formats (MP3)**: One generation of re-encoding - minimal quality loss

## File Extension Preservation

The tool preserves your original file extensions:
- `.mp3` → `.mp3`
- `.flac` → `.flac`
- `.aiff` → `.aiff`
- `.wav` → `.wav`

## Platform Support

- **Windows**: Yes (requires FFmpeg and bs1770gain installed)
- **Linux**: Yes
- **macOS**: Yes

## Examples

### Normalize a folder of FLAC files
```bash
python gain_sync.py --folder /home/user/music/album
```

### Revert to original loudness
```bash
python gain_sync.py --folder /home/user/music/album --invert
```
