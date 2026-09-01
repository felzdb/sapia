from pathlib import Path
import shutil

BASE_DIR = Path(__file__).resolve().parent.parent

TEMP_DIR = BASE_DIR / "temp"
UPLOAD_DIR = TEMP_DIR / "uploads"


def reset_temp_storage():
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


def get_upload_directory():
    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    return UPLOAD_DIR