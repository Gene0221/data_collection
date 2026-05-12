from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from common import (
    compute_reprojection_error,
    create_object_points,
    ensure_dir,
    find_corners,
    get_camera_paths,
    list_camera_images,
    load_config,
    save_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Calibrate one camera from a YAML config.")
    parser.add_argument("--config", required=True, help="Path to calibration YAML config.")
    parser.add_argument("--camera-id", required=True, help="Camera ID defined in config, such as cam0.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    camera_id = args.camera_id
    paths = get_camera_paths(config, camera_id)
    images = list_camera_images(config, camera_id)
    min_images = int(config.get("calibration", {}).get("min_images", 10))

    if len(images) < min_images:
        raise RuntimeError(
            f"Camera '{camera_id}' only has {len(images)} images, but config requires at least {min_images}."
        )

    object_points_template = create_object_points(config)
    object_points: list[np.ndarray] = []
    image_points: list[np.ndarray] = []
    used_images: list[str] = []
    image_size: tuple[int, int] | None = None

    save_vis = bool(config.get("calibration", {}).get("save_visualizations", True))
    if save_vis:
        ensure_dir(paths.corners_vis_dir)

    for image_path in images:
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"[WARN] Failed to read: {image_path}")
            continue

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if image_size is None:
            image_size = (gray.shape[1], gray.shape[0])

        success, corners = find_corners(gray, config)
        if not success or corners is None:
            print(f"[INFO] Corners not found: {image_path.name}")
            continue

        object_points.append(object_points_template.copy())
        image_points.append(corners)
        used_images.append(image_path.name)
        print(f"[OK] Corners detected: {image_path.name}")

        if save_vis:
            vis = image.copy()
            cv2.drawChessboardCorners(vis, tuple(config["board"]["pattern_size"]), corners, True)
            cv2.imwrite(str(paths.corners_vis_dir / image_path.name), vis)

    if image_size is None:
        raise RuntimeError(f"No valid images found for camera '{camera_id}'.")
    if len(image_points) < min_images:
        raise RuntimeError(
            f"Camera '{camera_id}' only has {len(image_points)} valid corner detections, "
            f"but config requires at least {min_images}."
        )

    rms, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        object_points,
        image_points,
        image_size,
        None,
        None,
    )

    alpha = float(config.get("calibration", {}).get("undistort_alpha", 0.0))
    optimal_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
        camera_matrix, dist_coeffs, image_size, alpha, image_size
    )
    mean_error, per_image_errors = compute_reprojection_error(
        object_points, image_points, rvecs, tvecs, camera_matrix, dist_coeffs
    )

    result = {
        "camera_id": camera_id,
        "image_size": {"width": image_size[0], "height": image_size[1]},
        "board": config["board"],
        "num_input_images": len(images),
        "num_used_images": len(used_images),
        "used_images": used_images,
        "rms": float(rms),
        "mean_reprojection_error": mean_error,
        "per_image_reprojection_error": per_image_errors,
        "camera_matrix": camera_matrix.tolist(),
        "dist_coeffs": dist_coeffs.tolist(),
        "optimal_camera_matrix": optimal_camera_matrix.tolist(),
        "roi": {"x": int(roi[0]), "y": int(roi[1]), "w": int(roi[2]), "h": int(roi[3])},
        "rvecs": [rvec.tolist() for rvec in rvecs],
        "tvecs": [tvec.tolist() for tvec in tvecs],
    }

    ensure_dir(paths.output_dir)
    save_json(paths.calibration_file, result)
    print(f"[DONE] Calibration saved to: {paths.calibration_file}")
    print(f"[DONE] RMS error: {rms:.6f}")
    print(f"[DONE] Mean reprojection error: {mean_error:.6f}")


if __name__ == "__main__":
    main()
