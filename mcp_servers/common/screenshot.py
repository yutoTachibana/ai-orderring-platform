"""スクリーンショット管理"""
from pathlib import Path


SCREENSHOT_DIR = Path("/app/screenshots")


def ensure_screenshot_dir(system_name: str) -> Path:
    dir_path = SCREENSHOT_DIR / system_name
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_screenshot_path(system_name: str, filename: str) -> str:
    dir_path = ensure_screenshot_dir(system_name)
    return str(dir_path / filename)
