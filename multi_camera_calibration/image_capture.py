import pyrealsense2 as rs
import numpy as np
import cv2
from pathlib import Path

# =========================
# 配置：填入两台相机序列号
# =========================
CAMERAS = {
    "camera_a": "213622073198",
    "camera_b": "337122072369",
}

WIDTH  = 640
HEIGHT = 480
FPS    = 30


def capture_images(camera_name: str, serial: str):
    """
    为单台相机采集标定图像。
    空格保存，ESC 退出。
    """
    save_dir = Path("images") / camera_name
    save_dir.mkdir(parents=True, exist_ok=True)

    pipeline = rs.pipeline()
    config   = rs.config()

    config.enable_device(serial)
    config.enable_stream(
        rs.stream.color,
        WIDTH, HEIGHT,
        rs.format.bgr8, FPS
    )

    pipeline.start(config)

    count    = 0
    window   = f"Capture - {camera_name} (SPACE=保存  ESC=退出)"

    print(f"\n{'='*45}")
    print(f"  相机：{camera_name}  SN={serial}")
    print(f"  保存目录：{save_dir}")
    print(f"  SPACE 保存，ESC 退出")
    print(f"{'='*45}\n")

    try:

        while True:

            frames = pipeline.wait_for_frames()
            color_frame = frames.get_color_frame()

            if not color_frame:
                continue

            image = np.asanyarray(color_frame.get_data())

            # 叠加已保存数量提示
            vis = image.copy()
            cv2.putText(
                vis,
                f"Saved: {count}  |  SPACE=Save  ESC=Exit",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (0, 255, 0), 2
            )
            cv2.imshow(window, vis)

            key = cv2.waitKey(1) & 0xFF

            # 空格保存
            if key == 32:
                filename = save_dir / f"{count:04d}.png"
                cv2.imwrite(str(filename), image)
                print(f"  [保存] {filename}")
                count += 1

            # ESC 退出
            elif key == 27:
                break

    finally:
        pipeline.stop()
        cv2.destroyAllWindows()

    print(f"  完成：共保存 {count} 张图像\n")


# =========================
# 依次采集 Camera A 和 Camera B
# =========================
if __name__ == "__main__":

    for name, serial in CAMERAS.items():
        input(f"\n准备采集 {name}（SN={serial}），按 Enter 开始...")
        capture_images(name, serial)

    print("图像采集完成")
