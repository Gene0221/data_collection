from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from common import get_camera_ids, load_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calibrate all enabled cameras from a YAML config.")
    parser.add_argument("--config", required=True, help="Path to calibration YAML config.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    camera_ids = get_camera_ids(config)
    script_path = Path(__file__).resolve().parent / "calibrate_camera.py"

    for camera_id in camera_ids:
        print(f"\n===== Calibrating {camera_id} =====")
        result = subprocess.run(
            [sys.executable, str(script_path), "--config", args.config, "--camera-id", camera_id],
            check=False,
        )
        if result.returncode != 0:
            raise SystemExit(f"Calibration failed for camera '{camera_id}'.")


if __name__ == "__main__":
    main()
