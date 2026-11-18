#!/usr/bin/env python3
"""
Test the gain sync module with sample data.
"""

import sys
import json
from pathlib import Path
from gain_sync import AudioFile, calculate_adjustments, log_change


def test_audio_file():
    """Test AudioFile dataclass."""
    print("Test 1: AudioFile dataclass")
    
    audio = AudioFile(
        path=Path("/test/file.wav"),
        loudness=-12.5,
        peak=-1.0,
        adjustment=-1.5
    )
    
    assert audio.loudness == -12.5
    assert audio.adjustment == -1.5
    
    # Test serialization
    d = audio.to_dict()
    assert d["path"] == "/test/file.wav"
    assert d["loudness"] == -12.5
    
    print("  ✓ AudioFile works")


def test_calculate_adjustments():
    """Test adjustment calculation."""
    print("\nTest 2: Calculate adjustments")
    
    files = [
        AudioFile(path=Path("/test1.wav"), loudness=-10.0),
        AudioFile(path=Path("/test2.wav"), loudness=-12.0),
        AudioFile(path=Path("/test3.wav"), loudness=-14.0),
        AudioFile(path=Path("/test4.wav"), loudness=-16.0),
        AudioFile(path=Path("/test5.wav"), loudness=-18.0),
    ]
    
    median = calculate_adjustments(files)
    
    # Median should be -14 (3rd file in sorted list)
    assert median == -14.0
    
    # First file: -10 + adjustment = -14, so adjustment = -4
    assert files[0].adjustment == -4.0
    
    # Third file: -14 + adjustment = -14, so adjustment = 0
    assert files[2].adjustment == 0.0
    
    print("  ✓ Adjustment calculation works")


def test_log_change():
    """Test logging changes."""
    print("\nTest 3: Log change")
    
    # Create test file first
    test_file = Path("/tmp/test_gain_sync_file.wav")
    test_file.touch()
    
    # Clean up test log
    log_file = Path("test_changes.log")
    if log_file.exists():
        log_file.unlink()
    
    audio = AudioFile(
        path=test_file,
        loudness=-12.0,
        peak=-1.0,
        adjustment=-2.0
    )
    
    # Log the change
    log_change(audio, -2.0, log_file="test_changes.log")
    
    # Verify log entry
    assert log_file.exists()
    
    with open(log_file, 'r') as f:
        entry = json.loads(f.readline())
        assert entry["path"] == str(test_file)
        assert entry["adjustment"] == -2.0
        # "action" field removed from log
    
    # Cleanup
    log_file.unlink()
    test_file.unlink()
    
    print("  ✓ Logging works")


def run_all_tests():
    """Run all tests."""
    print("Running tests for Gain Sync\n")
    
    try:
        test_audio_file()
        test_calculate_adjustments()
        test_log_change()
        print("\n✅ All tests passed!")
        return True
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
