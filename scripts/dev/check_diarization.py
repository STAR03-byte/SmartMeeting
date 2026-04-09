"""
Speaker Diarization Health Check Script
Run this script to verify all configurations are correct
"""
import sys
import os
# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
sys.path.insert(0, os.path.abspath(backend_path))

def check_configuration():
    """Check if configuration is correct"""
    print("=" * 60)
    print("Speaker Diarization Health Check")
    print("=" * 60)
    
    # 1. 检查 pyannote 是否安装
    print("\n1. Checking pyannote.audio installation...")
    try:
        import pyannote.audio
        print("   [OK] pyannote.audio is installed")
    except ImportError:
        print("   [FAIL] pyannote.audio is not installed")
        print("   Fix: pip install pyannote.audio>=3.1.0")
        return False
    
    print("\n2. Checking configuration...")
    from app.core.config import settings

    checks = {
        "ENABLE_SPEAKER_DIARIZATION": settings.enable_speaker_diarization,
        "PYANNOTE_HF_TOKEN": bool(settings.pyannote_hf_token),
        "HF_ENDPOINT": settings.hf_endpoint,
        "PYANNOTE_REQUIRE_GPU": settings.pyannote_require_gpu,
    }

    all_ok = True
    for name, value in checks.items():
        status = "[OK]" if value else "[WARN]"
        print(f"   {status} {name}: {value}")
        if not value and name != "PYANNOTE_REQUIRE_GPU":
            all_ok = False

    print("\n3. Checking model loading...")
    try:
        from app.services.speaker_diarization_service import speaker_diarization_service
        available = speaker_diarization_service._ensure_pyannote()
        if available:
            print("   [OK] pyannote is available")
            speaker_diarization_service.preload_pipeline()
            if speaker_diarization_service._pipeline is not None:
                print("   [OK] Speaker diarization model is loaded")
            else:
                print("   [WARN] Model not loaded (may need download on first run)")
        else:
            print("   [FAIL] pyannote is not available")
            all_ok = False
    except Exception as e:
        print(f"   [FAIL] Model loading failed: {e}")
        all_ok = False

    print("\n4. Checking faster-whisper...")
    try:
        import faster_whisper
        print("   [OK] faster-whisper is installed")
    except ImportError:
        print("   [WARN] faster-whisper not installed (will use whisper fallback)")

    print("\n" + "=" * 60)
    if all_ok:
        print("[PASS] All checks passed! Speaker diarization is ready")
        print("\nNext step: Restart backend service and upload audio to test")
    else:
        print("[FAIL] Some checks failed, please fix the issues above")
    print("=" * 60)
    
    return all_ok

if __name__ == "__main__":
    success = check_configuration()
    sys.exit(0 if success else 1)
