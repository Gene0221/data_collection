# Multi Camera Calibration

This directory contains the non-ROS dual-D435i workflow for:

- synchronized RGB pair capture
- offline RGB extrinsics estimation
- online AprilTag pose-delta tracking in camera A coordinates

## Entry Points

```bash
python multi_camera_calibration/capture_two_d435i_rgb_pairs.py --list-devices
python multi_camera_calibration/capture_two_d435i_rgb_pairs.py
python multi_camera_calibration/estimate_rgb_extrinsics.py
python multi_camera_calibration/track_apriltag_pose_deltas.py
```

## Dependencies

Install Python dependencies with:

```bash
python -m pip install -r multi_camera_calibration/requirements.txt
```

You also need a working `librealsense` / `pyrealsense2` environment.

## Config Files

- [config/capture.yaml](C:/Users/zhj80/OneDrive/Desktop/Master%20Course%20Material/research/data_collection/multi_camera_calibration/config/capture.yaml)
- [config/extrinsics.yaml](C:/Users/zhj80/OneDrive/Desktop/Master%20Course%20Material/research/data_collection/multi_camera_calibration/config/extrinsics.yaml)
- [config/apriltag_tracking.yaml](C:/Users/zhj80/OneDrive/Desktop/Master%20Course%20Material/research/data_collection/multi_camera_calibration/config/apriltag_tracking.yaml)

## RGB Capture

`capture_two_d435i_rgb_pairs.py` captures synchronized RGB image pairs from camera A and camera B.

It uses:

- dual frame buffers
- minimum host-timestamp difference matching
- live preview
- image pair saving plus metadata export

The capture config stores:

- camera A serial number
- camera B serial number
- RGB width / height / fps
- preview width
- warmup frames
- startup timeout
- output root
- buffer size
- maximum allowed timestamp delta

## RGB Extrinsics

`estimate_rgb_extrinsics.py` assumes:

- camera A RGB intrinsics are already calibrated
- camera B RGB intrinsics are already calibrated
- synchronized checkerboard RGB image pairs are already captured

It estimates camera B in camera A coordinates and writes:

- `<dataset_dir>/rgb_extrinsics_result.json`
- `<dataset_dir>/rgb_extrinsics_result.yaml`

The result includes:

- per-pair board pose results
- per-pair `transform_a_b`
- averaged final `rotation_matrix_a_b`
- averaged final `translation_vector_a_b`
- `4x4` homogeneous transform
- TF-style translation and quaternion output

Session selection for extrinsics:

- the script works on `output/<session_name>`
- you can set `output.session_name` in [config/extrinsics.yaml](C:/Users/zhj80/OneDrive/Desktop/Master%20Course%20Material/research/data_collection/multi_camera_calibration/config/extrinsics.yaml)
- if it is empty, the script prompts for `session_name` in the terminal

## AprilTag Pose Deltas

`track_apriltag_pose_deltas.py` performs real-time tracking for multiple AprilTags.

Current behavior:

- default AprilTag family is `tag36h11`
- two D435i RGB streams run online
- poses are unified into camera A coordinates
- if both cameras see the tag, camera A is preferred
- if camera A misses the tag and camera B sees it, the pose is transformed from B to A
- if neither camera sees the tag, that tag is marked missing for the current frame
- each tracked tag is recorded independently
- pose deltas are computed between adjacent valid frames

For each tracked tag, the output includes:

- current `4x4` pose matrix in camera A coordinates
- adjacent-frame `4x4` delta transform
- adjacent-frame translation delta
- adjacent-frame rotation delta quaternion

Tracking outputs:

- `<session_dir>/tag_pose_deltas.jsonl`
- `<session_dir>/tracking_summary.json`

Session selection for tracking:

- the script prompts for `session_name` if `output.session_name` is empty
- it writes tracking logs into `output/<session_name>`
- it loads the extrinsics result from `output/<session_name>/rgb_extrinsics_result.json` by default
- you can still override the extrinsics path in [config/apriltag_tracking.yaml](C:/Users/zhj80/OneDrive/Desktop/Master%20Course%20Material/research/data_collection/multi_camera_calibration/config/apriltag_tracking.yaml) if needed
