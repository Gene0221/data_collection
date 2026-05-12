from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import yaml


@dataclass
class CameraPaths:
    image_dir: Path
    output_dir: Path
    calibration_file: Path
    corners_vis_dir: Path
    undistort_dir: Path


def load_config(config_path: str | Path) -> dict[str, Any]:
    config_file = Path(config_path).resolve()
    with config_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError("YAML config must be a mapping.")

    data["_config_dir"] = config_file.parent
    return data


def resolve_path(base_dir: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()


def get_camera_ids(config: dict[str, Any]) -> list[str]:
    cameras = config.get("cameras", {})
    return [camera_id for camera_id, camera_cfg in cameras.items() if camera_cfg.get("enabled", True)]


def get_camera_config(config: dict[str, Any], camera_id: str) -> dict[str, Any]:
    cameras = config.get("cameras", {})
    if camera_id not in cameras:
        raise KeyError(f"Camera '{camera_id}' is not defined in config.")
    return cameras[camera_id]


def get_camera_paths(config: dict[str, Any], camera_id: str) -> CameraPaths:
    config_dir = Path(config["_config_dir"])
    camera_cfg = get_camera_config(config, camera_id)
    calibration_cfg = config.get("calibration", {})
    undistort_cfg = config.get("undistort", {})

    image_dir = resolve_path(config_dir, camera_cfg["image_dir"])
    output_dir = resolve_path(config_dir, camera_cfg["output_dir"])
    corners_vis_dir = output_dir / calibration_cfg.get("visualization_dirname", "corners_vis")
    undistort_dir = output_dir / undistort_cfg.get("output_dirname", "undistorted")
    calibration_file = output_dir / "calibration_result.json"

    return CameraPaths(
        image_dir=image_dir,
        output_dir=output_dir,
        calibration_file=calibration_file,
        corners_vis_dir=corners_vis_dir,
        undistort_dir=undistort_dir,
    )


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def list_camera_images(config: dict[str, Any], camera_id: str) -> list[Path]:
    camera_cfg = get_camera_config(config, camera_id)
    paths = get_camera_paths(config, camera_id)
    pattern = camera_cfg.get("image_pattern", "*.jpg")
    images = sorted(paths.image_dir.glob(pattern))
    return [p for p in images if p.is_file()]


def create_object_points(config: dict[str, Any]) -> np.ndarray:
    board_cfg = config["board"]
    cols, rows = board_cfg["pattern_size"]
    square_size = float(board_cfg["square_size_mm"])

    objp = np.zeros((rows * cols, 3), np.float32)
    grid = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2)
    objp[:, :2] = grid
    objp *= square_size
    return objp


def get_find_chessboard_flags(config: dict[str, Any]) -> int:
    corner_cfg = config.get("corner_detection", {})
    flags = 0
    if corner_cfg.get("adaptive_thresh", True):
        flags |= cv2.CALIB_CB_ADAPTIVE_THRESH
    if corner_cfg.get("normalize_image", True):
        flags |= cv2.CALIB_CB_NORMALIZE_IMAGE
    if corner_cfg.get("fast_check", False):
        flags |= cv2.CALIB_CB_FAST_CHECK
    return flags


def find_corners(gray: np.ndarray, config: dict[str, Any]) -> tuple[bool, np.ndarray | None]:
    board_cfg = config["board"]
    pattern_size = tuple(board_cfg["pattern_size"])
    corner_cfg = config.get("corner_detection", {})
    use_sb = corner_cfg.get("use_find_chessboard_sb", True)

    if use_sb:
        success, corners = cv2.findChessboardCornersSB(gray, pattern_size, None)
    else:
        flags = get_find_chessboard_flags(config)
        success, corners = cv2.findChessboardCorners(gray, pattern_size, flags)

    if not success or corners is None:
        return False, None

    subpix_cfg = corner_cfg.get("subpix", {})
    if subpix_cfg.get("enabled", True) and not use_sb:
        win_size = tuple(subpix_cfg.get("win_size", [11, 11]))
        zero_zone = tuple(subpix_cfg.get("zero_zone", [-1, -1]))
        criteria_cfg = subpix_cfg.get("criteria", {})
        criteria = (
            cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
            int(criteria_cfg.get("max_iter", 30)),
            float(criteria_cfg.get("epsilon", 0.001)),
        )
        corners = cv2.cornerSubPix(gray, corners, win_size, zero_zone, criteria)

    return True, corners


def save_json(path: Path, data: dict[str, Any]) -> None:
    ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def compute_reprojection_error(
    object_points: list[np.ndarray],
    image_points: list[np.ndarray],
    rvecs: list[np.ndarray],
    tvecs: list[np.ndarray],
    camera_matrix: np.ndarray,
    dist_coeffs: np.ndarray,
) -> tuple[float, list[float]]:
    per_image_errors: list[float] = []
    for objp, imgp, rvec, tvec in zip(object_points, image_points, rvecs, tvecs):
        reprojected, _ = cv2.projectPoints(objp, rvec, tvec, camera_matrix, dist_coeffs)
        error = cv2.norm(imgp, reprojected, cv2.NORM_L2) / len(reprojected)
        per_image_errors.append(float(error))
    mean_error = float(sum(per_image_errors) / len(per_image_errors)) if per_image_errors else 0.0
    return mean_error, per_image_errors
