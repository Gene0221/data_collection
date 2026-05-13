#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import rospy
from cv_bridge import CvBridge
from message_filters import ApproximateTimeSynchronizer, Subscriber
from sensor_msgs.msg import Image


@dataclass
class PairSample:
    image_a: np.ndarray
    image_b: np.ndarray
    stamp_a: float
    stamp_b: float


class PairCaptureNode:
    def __init__(self) -> None:
        self.bridge = CvBridge()
        self.latest_sample: Optional[PairSample] = None
        self.saved_count = 0

        self.topic_a = rospy.get_param("~camera_a/image_topic", rospy.get_param("/camera_a/image_topic"))
        self.topic_b = rospy.get_param("~camera_b/image_topic", rospy.get_param("/camera_b/image_topic"))
        self.queue_size = int(rospy.get_param("~synchronization/queue_size", rospy.get_param("/synchronization/queue_size", 10)))
        self.slop_seconds = float(rospy.get_param("~synchronization/slop_seconds", rospy.get_param("/synchronization/slop_seconds", 0.03)))
        self.session_name = str(rospy.get_param("~capture/session_name", rospy.get_param("/capture/session_name", "sample_session")))
        self.output_root = Path(str(rospy.get_param("~capture/output_root", rospy.get_param("/capture/output_root", "/tmp/two_camera_rgb_extrinsic"))))
        self.preview_width = int(rospy.get_param("~capture/preview_width", rospy.get_param("/capture/preview_width", 1600)))
        self.image_extension = str(rospy.get_param("~capture/image_extension", rospy.get_param("/capture/image_extension", ".png")))

        self.dataset_dir = self.output_root / self.session_name
        self.camera_a_dir = self.dataset_dir / "camera_a"
        self.camera_b_dir = self.dataset_dir / "camera_b"
        self.metadata_path = self.dataset_dir / "pairs_metadata.json"
        self.window_name = "Two-Camera RGB Capture"
        self.metadata: list[dict[str, float | int | str]] = []

        self.camera_a_dir.mkdir(parents=True, exist_ok=True)
        self.camera_b_dir.mkdir(parents=True, exist_ok=True)

        sub_a = Subscriber(self.topic_a, Image)
        sub_b = Subscriber(self.topic_b, Image)
        self.sync = ApproximateTimeSynchronizer([sub_a, sub_b], self.queue_size, self.slop_seconds)
        self.sync.registerCallback(self.callback)

    def callback(self, msg_a: Image, msg_b: Image) -> None:
        image_a = self.bridge.imgmsg_to_cv2(msg_a, desired_encoding="bgr8")
        image_b = self.bridge.imgmsg_to_cv2(msg_b, desired_encoding="bgr8")
        self.latest_sample = PairSample(
            image_a=image_a,
            image_b=image_b,
            stamp_a=msg_a.header.stamp.to_sec(),
            stamp_b=msg_b.header.stamp.to_sec(),
        )

    def run(self) -> None:
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        rate = rospy.Rate(30)
        rospy.loginfo("Press S to save a synchronized pair, Q to quit.")

        while not rospy.is_shutdown():
            if self.latest_sample is not None:
                preview = self.build_preview(self.latest_sample)
                cv2.imshow(self.window_name, preview)
                key = cv2.waitKey(1) & 0xFF
                if key in {ord("q"), ord("Q")}:
                    break
                if key in {ord("s"), ord("S")}:
                    self.save_current_sample(self.latest_sample)
            rate.sleep()

        self.write_metadata()
        cv2.destroyAllWindows()

    def build_preview(self, sample: PairSample) -> np.ndarray:
        panel_a = self.annotate(sample.image_a.copy(), "Camera A RGB")
        panel_b = self.annotate(sample.image_b.copy(), "Camera B RGB")
        width_each = max(1, self.preview_width // 2)
        panel_a = resize_to_width(panel_a, width_each)
        panel_b = resize_to_width(panel_b, width_each)
        target_height = min(panel_a.shape[0], panel_b.shape[0])
        panel_a = resize_to_height(panel_a, target_height)
        panel_b = resize_to_height(panel_b, target_height)
        preview = cv2.hconcat([panel_a, panel_b])
        status = f"Saved pairs: {self.saved_count} | Keys: S save, Q quit"
        cv2.putText(preview, status, (20, max(40, preview.shape[0] - 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
        return preview

    def annotate(self, image: np.ndarray, title: str) -> np.ndarray:
        cv2.putText(image, title, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)
        return image

    def save_current_sample(self, sample: PairSample) -> None:
        self.saved_count += 1
        index = self.saved_count
        filename_a = f"camera_a_{index:04d}{self.image_extension}"
        filename_b = f"camera_b_{index:04d}{self.image_extension}"
        path_a = self.camera_a_dir / filename_a
        path_b = self.camera_b_dir / filename_b
        cv2.imwrite(str(path_a), sample.image_a)
        cv2.imwrite(str(path_b), sample.image_b)
        time_delta = abs(sample.stamp_a - sample.stamp_b)
        self.metadata.append(
            {
                "pair_index": index,
                "camera_a_image": filename_a,
                "camera_b_image": filename_b,
                "camera_a_stamp": sample.stamp_a,
                "camera_b_stamp": sample.stamp_b,
                "timestamp_delta_seconds": time_delta,
            }
        )
        rospy.loginfo("Saved pair %04d with timestamp delta %.6f s", index, time_delta)

    def write_metadata(self) -> None:
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "session_name": self.session_name,
            "camera_a_topic": self.topic_a,
            "camera_b_topic": self.topic_b,
            "saved_pair_count": self.saved_count,
            "pairs": self.metadata,
        }
        self.metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        rospy.loginfo("Wrote metadata to %s", self.metadata_path)


def resize_to_width(image: np.ndarray, width: int) -> np.ndarray:
    scale = width / image.shape[1]
    height = max(1, int(image.shape[0] * scale))
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)


def resize_to_height(image: np.ndarray, height: int) -> np.ndarray:
    scale = height / image.shape[0]
    width = max(1, int(image.shape[1] * scale))
    return cv2.resize(image, (width, height), interpolation=cv2.INTER_AREA)


def main() -> None:
    rospy.init_node("capture_rgb_pairs")
    node = PairCaptureNode()
    node.run()


if __name__ == "__main__":
    main()
