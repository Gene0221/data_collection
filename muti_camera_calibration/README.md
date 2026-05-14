# Multi Camera Calibration

This directory is reserved for the non-ROS multi-camera calibration workflow.

Current scope:

- dual D435i RGB pair capture
- dual-buffer frame caching
- minimum host-timestamp difference matching
- image pair and metadata saving
- offline RGB extrinsics estimation for camera B in camera A coordinates

Current entry point:

```bash
python muti_camera_calibration/capture_two_d435i_rgb_pairs.py --list-devices
python muti_camera_calibration/capture_two_d435i_rgb_pairs.py
python muti_camera_calibration/estimate_rgb_extrinsics.py
```

Default configuration file:

- [config/capture.yaml](C:/Users/zhj80/OneDrive/Desktop/Master%20Course%20Material/research/data_collection/muti_camera_calibration/config/capture.yaml)
- [config/extrinsics.yaml](C:/Users/zhj80/OneDrive/Desktop/Master%20Course%20Material/research/data_collection/muti_camera_calibration/config/extrinsics.yaml)

It currently stores:

- camera A serial number
- camera B serial number
- RGB width / height / fps
- preview width
- warmup frames
- startup timeout
- output root
- buffer size
- maximum allowed timestamp delta

Extrinsics estimation config stores:

- dataset directory containing `camera_a/` and `camera_b/`
- camera A RGB intrinsics file path
- camera B RGB intrinsics file path
- checkerboard rows / cols / square size
- output file name stem
- TF frame names
- minimum valid pair count

Extrinsics workflow:

1. Capture synchronized RGB image pairs with `capture_two_d435i_rgb_pairs.py`.
2. Make sure camera A and camera B RGB intrinsics are already calibrated.
3. Update [config/extrinsics.yaml](C:/Users/zhj80/OneDrive/Desktop/Master%20Course%20Material/research/data_collection/muti_camera_calibration/config/extrinsics.yaml).
4. Run:

```bash
python muti_camera_calibration/estimate_rgb_extrinsics.py
```

Outputs:

- `<dataset_dir>/rgb_extrinsics_result.json`
- `<dataset_dir>/rgb_extrinsics_result.yaml`

The result includes:

- per-pair board pose results
- per-pair `transform_a_b`
- averaged final `rotation_matrix_a_b`
- averaged final `translation_vector_a_b`
- `4x4` homogeneous transform
- TF-style translation and quaternion output
