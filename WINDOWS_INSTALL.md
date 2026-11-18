# Windows Installation Guide

This guide shows how to install the requirements for Gain Sync on Windows.

## Step 1: Install FFmpeg

1. Download FFmpeg from: https://ffmpeg.org/download.html
2. Choose the Windows build (e.g., from gyan.dev)
3. Extract to `C:\ffmpeg`
4. Add to PATH: `C:\ffmpeg\bin`

## Step 2: Install bs1770gain

1. Download from: https://github.com/Mayou31/bs1770gain/releases
2. Download the Windows binary (e.g., `bs1770gain-0.4.1-win64.exe`)
3. Place in a folder in your PATH (e.g., `C:\Program Files\bs1770gain\`)
4. Rename to `bs1770gain.exe` or add the folder to PATH

## Step 3: Verify Installation

Open Command Prompt and run:

```cmd
ffmpeg -version
bs1770gain --help
```

## Step 4: Run Gain Sync

```cmd
cd C:\path\to\gain-sync
python gain_sync.py --folder "C:\path\to\your\music"
```

## Troubleshooting

- If `ffmpeg` or `bs1770gain` aren't recognized, restart your terminal after installing
- Make sure both tools are in your system PATH
- Run as Administrator if you encounter permission errors
