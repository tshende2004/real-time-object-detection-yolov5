"""
main.py
-------
CCTV anomaly detection pipeline controller.

All detection logic is handled inside detector.py

"""

import cv2
import logging

from detector import Detector


# ============================================================
# CONFIG
# ============================================================

VIDEO_PATH = "videos/sudden_running.avi"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger("CCTVSystem.Main")


# ============================================================
# INITIALIZE DETECTOR
# ============================================================

logger.info("Initializing detector...")

detector = Detector()

logger.info("Detector ready")


# ============================================================
# OPEN VIDEO
# ============================================================

logger.info(f"Opening video: {VIDEO_PATH}")

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    raise FileNotFoundError(
        f"Cannot open video: {VIDEO_PATH}"
    )

total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps          = cap.get(cv2.CAP_PROP_FPS)

logger.info(f"Video opened: {total_frames} frames @ {fps:.1f} FPS")


# ============================================================
# VIDEO LOOP
# ============================================================

frame_count = 0

while True:

    ret, frame = cap.read()

    if not ret:
        logger.info("Video ended")
        break

    frame_count += 1

    # -----------------------------------------
    # Send frame to detector
    # BUG 3 FIX: unpack tuple (frame, anomalies)
    # -----------------------------------------
    processed_frame, active_anomalies = detector.process(
        frame,
        VIDEO_PATH
    )

    # -----------------------------------------
    # Display result
    # -----------------------------------------
    cv2.imshow(
        "CCTV Anomaly System",
        processed_frame
    )

    # ESC to quit
    if cv2.waitKey(1) & 0xFF == 27:
        logger.info("ESC pressed")
        break


# ============================================================
# CLEANUP
# ============================================================

cap.release()
cv2.destroyAllWindows()
logger.info("System stopped")