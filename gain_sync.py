#!/usr/bin/env python3
"""
Gain Sync - Normalize audio files by EBU R128 loudness and peak levels.

Requirements:
    - ffmpeg
    - bs1770gain

Usage:
    python gain_sync.py --folder /path/to/audio/folder
    python gain_sync.py --folder /path/to/audio/folder --invert
"""

import argparse
import json
import math
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Optional


@dataclass
class AudioFile:
    path: Path
    loudness: Optional[float] = None  # LUFS
    peak: Optional[float] = None  # dBFS
    adjustment: Optional[float] = None  # dB to apply
    original_loudness: Optional[float] = None
    original_peak: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "loudness": self.loudness,
            "peak": self.peak,
            "adjustment": self.adjustment,
            "original_loudness": self.original_loudness,
            "original_peak": self.original_peak,
        }


LOG_FILE = "changes.log"


def find_audio_files(folder: Path) -> List[Path]:
    """Find all audio files in folder."""
    extensions = {".wav", ".flac", ".aiff"}
    files = []
    for ext in extensions:
        files.extend(folder.glob(f"**/*{ext}"))
        files.extend(folder.glob(f"**/*{ext.upper()}"))
    return sorted(set(files))


def get_loudness_ffmpeg(path: Path) -> tuple:
    """Get loudness and peak using FFmpeg ebur128 filter."""
    cmd = [
        "ffmpeg", "-i", str(path),
        "-filter:a", "ebur128=peak=true",
        "-f", "null", "-"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    loudness = None
    peak = None
    
    for line in result.stderr.split('\n'):
        if 'I:' in line and 'LUFS' in line:
            # Extract LUFS value
            parts = line.split()
            for i, part in enumerate(parts):
                if part == 'I:' and i + 1 < len(parts):
                    try:
                        loudness = float(parts[i + 1])
                        break
                    except ValueError:
                        pass
        
        if 'Peak:' in line and 'dB' in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if part == 'Peak:' and i + 1 < len(parts):
                    try:
                        peak = float(parts[i + 1])
                        break
                    except ValueError:
                        pass
    
    return loudness, peak


def get_loudness_bs1770gain(path: Path) -> tuple:
    """Get loudness and peak using bs1770gain."""
    cmd = ["bs1770gain", "-p", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Parse bs1770gain output
    loudness = None
    peak = None
    
    for line in result.stdout.split('\n'):
        if 'LUFS' in line and 'I:' in line:
            try:
                loudness = float(line.split('I:')[1].split()[0])
            except (IndexError, ValueError):
                pass
        
        if 'Peak:' in line:
            try:
                peak = float(line.split('Peak:')[1].split()[0])
            except (IndexError, ValueError):
                pass
    
    return loudness, peak


def measure_file(filepath: Path) -> AudioFile:
    """Measure a single audio file."""
    audio = AudioFile(path=filepath)
    
    try:
        # Try bs1770gain first
        loudness, peak = get_loudness_bs1770gain(filepath)
        if loudness is None:
            loudness, peak = get_loudness_ffmpeg(filepath)
        
        audio.original_loudness = loudness
        audio.original_peak = peak
        audio.loudness = loudness
        audio.peak = peak
        
    except Exception as e:
        print(f"Error measuring {filepath}: {e}")
    
    return audio


def calculate_adjustments(files: List[AudioFile]) -> float:
    """Calculate adjustment gains to normalize to median loudness."""
    loudnesses = [f.loudness for f in files if f.loudness is not None]
    
    if not loudnesses:
        print("Error: No valid loudness measurements")
        return 0
    
    # Sort for median calculation
    sorted_loudnesses = sorted(loudnesses)
    n = len(sorted_loudnesses)
    
    if n % 2 == 0:
        median = (sorted_loudnesses[n // 2 - 1] + sorted_loudnesses[n // 2]) / 2
    else:
        median = sorted_loudnesses[n // 2]
    
    # Target LUFS (typical loud target)
    target_lufs = -14  # Common broadcast/Streaming target
    
    # Calculate adjustments
    for audio in files:
        if audio.loudness is not None:
            audio.adjustment = target_lufs - audio.loudness
    
    return median


def apply_normalization(audio: AudioFile) -> bool:
    """Apply normalization using FFmpeg while preserving the original file extension."""
    if audio.adjustment is None:
        print(f"Error: No adjustment for {audio.path}")
        return False
    
    # Calculate gain multiplier (dB to amplitude)
    gain_db = audio.adjustment
    gain_amp = 10 ** (gain_db / 20)
    original_ext = audio.path.suffix  # e.g., .mp3, .flac, .aiff
    output_path = audio.path.with_suffix(original_ext + ".tmp")
    
    cmd = [
        "ffmpeg", "-y", "-i", str(audio.path),
        "-af", f"volume={gain_amp}dB",
        str(output_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"FFmpeg error for {audio.path}: {result.stderr}")
            return False
        
        # Replace original file (preserving extension)
        backup_path = audio.path.with_suffix(original_ext + ".bak")
        audio.path.rename(backup_path)
        output_path.rename(audio.path)
        
        # Log the change
        log_change(audio, gain_db, True)
        
        return True
        
    except Exception as e:
        print(f"Error normalizing {audio.path}: {e}")
        return False


def invert_normalization(audio: AudioFile) -> bool:
    """Invert previous normalization using stored log."""
    if not LOG_FILE or not os.path.exists(LOG_FILE):
        print(f"Error: {LOG_FILE} not found for inversion")
        return False
    
    # Read log and find entry for this file
    try:
        with open(LOG_FILE, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get("path") == str(audio.path):
                        gain_db = entry.get("adjustment", 0)
                        # Apply inverse gain
                        return apply_adjustment(audio, -gain_db)
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"Error reading log: {e}")
    
    print(f"Error: No log entry found for {audio.path}")
    return False


def apply_adjustment(audio: AudioFile, gain_db: float) -> bool:
    """Apply a specific gain adjustment while preserving the original file extension."""
    gain_amp = 10 ** (gain_db / 20)
    original_ext = audio.path.suffix  # e.g., .mp3, .flac, .aiff
    output_path = audio.path.with_suffix(original_ext + ".tmp")
    
    cmd = [
        "ffmpeg", "-y", "-i", str(audio.path),
        "-af", f"volume={gain_amp}dB",
        str(output_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return False
        
        # Replace original file (preserving extension)
        backup_path = audio.path.with_suffix(original_ext + ".bak")
        audio.path.rename(backup_path)
        output_path.rename(audio.path)
        
        return True
        
    except Exception as e:
        print(f"Error applying adjustment: {e}")
        return False


def log_change(audio: AudioFile, gain_db: float, normalize: bool = True, log_file: str = LOG_FILE):
    """Log the change for potential inversion."""
    entry = {
        "path": str(audio.path),
        "adjustment": gain_db,
        "timestamp": str(audio.path.stat().st_mtime),
        "action": "normalize" if normalize else "invert",
        "original_loudness": audio.original_loudness,
        "original_peak": audio.original_peak,
    }
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def main():
    parser = argparse.ArgumentParser(description='Normalize audio files by EBU R128 loudness')
    parser.add_argument('--folder', '-f', required=True, help='Folder containing audio files')
    parser.add_argument('--invert', action='store_true', help='Invert previous normalizations')
    
    args = parser.parse_args()
    
    folder = Path(args.folder)
    
    if not folder.exists():
        print(f"Error: Folder not found: {folder}")
        return 1
    
    print(f"Scanning folder: {folder}")
    
    # Find audio files
    audio_files = find_audio_files(folder)
    print(f"Found {len(audio_files)} audio files")
    
    if not audio_files:
        print("No audio files found")
        return 0
    
    # Measure files
    print("Measuring loudness...")
    files = [measure_file(path) for path in audio_files]
    
    # Check if inverting
    if args.invert:
        print("Inverting previous normalizations...")
        for audio in files:
            if invert_normalization(audio):
                print(f"  ✓ Inverted: {audio.path.name}")
            else:
                print(f"  ✗ Failed: {audio.path.name}")
        return 0
    
    # Calculate adjustments
    median_loudness = calculate_adjustments(files)
    print(f"Median loudness: {median_loudness:.2f} LUFS")
    print(f"Target loudness: -14 LUFS")
    
    # Apply normalization
    print("Applying normalization...")
    success_count = 0
    for audio in files:
        if apply_normalization(audio):
            print(f"  ✓ Normalized: {audio.path.name} ({audio.loudness:.2f} -> {audio.loudness + audio.adjustment:.2f} LUFS)")
            success_count += 1
        else:
            print(f"  ✗ Failed: {audio.path.name}")
    
    print(f"\nDone! Normalized {success_count}/{len(files)} files")
    print(f"Changes logged to: {LOG_FILE}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
