import cv2
import numpy as np
import glob
import json
from pathlib import Path

# =========================
# 棋盘格参数
# =========================
COLS = 6
ROWS = 9
SQUARE_MM = 24


def calibrate_camera(image_dir: str,
                     output_path: str,
                     camera_name: str = "camera",
                     cols: int = COLS,
                     rows: int = ROWS,
                     square_mm: float = SQUARE_MM):
    """
    参数：
        image_dir   : 标定图像目录（*.png）
        output_path : 输出 JSON 路径
        camera_name : 相机名称（仅用于打印提示）
        cols        : 棋盘格内角点列数
        rows        : 棋盘格内角点行数
        square_mm   : 格子实际边长（毫米）
    """
    print(f"\n{'=' * 45}")
    print(f"  标定相机：{camera_name}")
    print(f"  图像目录：{image_dir}")
    print(f"{'=' * 45}")

    # =========================
    # 世界坐标
    # =========================
    objp = np.zeros((rows * cols, 3), np.float32)
    objp[:, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2)
    objp *= square_mm

    objpoints = []
    imgpoints = []
    gray = None

    # =========================
    # 读取图像
    # =========================
    images = sorted(glob.glob(str(Path(image_dir) / "*.png")))

    if not images:
        raise FileNotFoundError(
            f"[{camera_name}] 未找到图像：{image_dir}/*.png")

    print(f"  找到 {len(images)} 张图像，开始检测角点...")

    for fname in images:

        img = cv2.imread(fname)
        if img is None:
            print(f"  [跳过] 无法读取：{fname}")
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        ret, corners = cv2.findChessboardCorners(
            gray, (cols, rows), None)

        if ret:
            crit = (cv2.TERM_CRITERIA_EPS +
                    cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
            corners = cv2.cornerSubPix(
                gray, corners, (11, 11), (-1, -1), crit)

            objpoints.append(objp)
            imgpoints.append(corners)

            cv2.drawChessboardCorners(img, (cols, rows), corners, ret)
            cv2.imshow(f"Corners - {camera_name}", img)
            cv2.waitKey(300)

    cv2.destroyAllWindows()

    valid = len(objpoints)
    print(f"  有效图像：{valid}/{len(images)}")

    if valid < 10:
        raise ValueError(
            f"[{camera_name}] 有效图像仅 {valid} 张，建议至少 15 张")

    # =========================
    # 标定
    # =========================
    rms, camera_matrix, dist_coeffs, rvecs, tvecs = \
        cv2.calibrateCamera(
            objpoints, imgpoints,
            gray.shape[::-1],
            None, None
        )

    print(f"  RMS 重投影误差：{rms:.4f} px"
          f"  {'良好' if rms < 0.5 else ' 偏高，建议补充采集'}")
    print(f"  Camera Matrix:\n{camera_matrix}")
    print(f"  Distortion: {dist_coeffs.ravel()}")

    # =========================
    # 保存 JSON
    # =========================
    data = {
        "camera_matrix": camera_matrix.tolist(),
        "dist_coeffs": dist_coeffs.tolist(),
        "width": gray.shape[1],
        "height": gray.shape[0],
        "distortion_model": "Brown_Conrady",
        "rms_error": float(rms),
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")

    print(f"  [DONE] 已保存：{output_path}")

    return data


# =========================
# 标定相机 A 和 相机 B
# =========================
if __name__ == "__main__":
    calibrate_camera(
        image_dir="images/camera_a",
        output_path="calibration/camera_a_calibration_result.json",
        camera_name="Camera A",
        cols=COLS,
        rows=ROWS,
        square_mm=SQUARE_MM,
    )

    calibrate_camera(
        image_dir="images/camera_b",
        output_path="calibration/camera_b_calibration_result.json",
        camera_name="Camera B",
        cols=COLS,
        rows=ROWS,
        square_mm=SQUARE_MM,
    )

    print("\两台相机内参标定全部完成")
