# Camera Calibration Toolkit

这套脚本按“`YAML` 配置驱动 + 多相机分目录管理”设计，适合同时管理 3 台相机的内参标定与去畸变流程。

## 目录约定

```text
camera_calibration/
  config/
    calibration.yaml
  data/
    raw/
      cam0/
      cam1/
      cam2/
    output/
      cam0/
      cam1/
      cam2/
  scripts/
    common.py
    calibrate_camera.py
    calibrate_all_cameras.py
    undistort_image.py
```

建议把三台相机的标定图分别放到：

- `data/raw/cam0`
- `data/raw/cam1`
- `data/raw/cam2`

每台相机的输出结果会分别保存到：

- `data/output/cam0`
- `data/output/cam1`
- `data/output/cam2`

这样每台相机都会拥有自己独立的：

- `calibration_result.json`
- `corners_vis/`
- `undistorted/`

## 配置文件

所有需要调整的参数都写在 [config/calibration.yaml](C:\Users\zhj80\OneDrive\Desktop\Master Course Material\research\camera_calibration\config\calibration.yaml)：

- `board.pattern_size`
  棋盘格内角点数量，例如 `[9, 6]`
- `board.square_size_mm`
  每个小方格的实际边长，单位 `mm`
- `corner_detection`
  角点检测参数
- `calibration.min_images`
  每台相机至少要用多少张有效标定图
- `cameras.cam0/cam1/cam2`
  每台相机的输入目录、输出目录、文件匹配规则

注意：

- `pattern_size` 是内角点数量，不是黑白格数量
- 如果你的图片是 `png`，把 `image_pattern` 改成 `*.png`

## 运行方式

先安装依赖：

```bash
pip install opencv-python pyyaml numpy
```

标定单台相机：

```bash
python scripts/calibrate_camera.py --config config/calibration.yaml --camera-id cam0
```

一次标定所有启用相机：

```bash
python scripts/calibrate_all_cameras.py --config config/calibration.yaml
```

对单张图去畸变：

```bash
python scripts/undistort_image.py --config config/calibration.yaml --camera-id cam0 --input path/to/test.jpg
```

对一个目录批量去畸变：

```bash
python scripts/undistort_image.py --config config/calibration.yaml --camera-id cam0 --input path/to/image_dir
```

## 输出说明

每台相机标定完成后，会生成：

- `camera_matrix`
  相机内参矩阵
- `dist_coeffs`
  畸变系数
- `optimal_camera_matrix`
  去畸变使用的优化内参
- `roi`
  去畸变后建议裁剪区域
- `rms`
  OpenCV 返回的 RMS 标定误差
- `mean_reprojection_error`
  平均重投影误差

## 拍摄建议

- 每台相机至少采集 `15` 到 `30` 张图片
- 标定板尽量覆盖画面中心、边缘、近处、远处
- 多拍一些倾斜姿态，避免全部正视
- 避免模糊、过曝、强反光
