# Multi Camera Calibration

This directory is reserved for the non-ROS multi-camera calibration workflow.

Current scope:

- dual D435i RGB pair capture
- dual-buffer frame caching
- minimum host-timestamp difference matching
- image pair and metadata saving

Current entry point:

```bash
python muti_camera_calibration/capture_two_d435i_rgb_pairs.py --list-devices
python muti_camera_calibration/capture_two_d435i_rgb_pairs.py
```

Default configuration file:

- [config/capture.yaml](C:/Users/zhj80/OneDrive/Desktop/Master%20Course%20Material/research/data_collection/muti_camera_calibration/config/capture.yaml)

It currently stores:

- expected number of connected cameras
- camera A serial number
- camera B serial number
- RGB width / height / fps
- preview width
- warmup frames
- startup timeout
- output root
- buffer size
- maximum allowed timestamp delta
