# Real-Time Object Detection with YOLOv5

Real-time object detection system built on a pre-trained YOLOv5 model, achieving stable inference at 20+ FPS on live video streams, with bounding boxes and confidence scores rendered via OpenCV.

## Overview

This project detects and localizes multiple object classes in real time from a video feed (webcam or file), overlaying bounding boxes and confidence scores on each frame.

## Tech Stack

- **Python**
- **YOLOv5** — pre-trained object detection model
- **OpenCV** — video capture and frame rendering
- **TensorFlow**

## Features

- Real-time inference at 20+ FPS on standard video streams
- Bounding box + confidence score overlay for each detected object
- Works on live webcam feed or pre-recorded video files

## How It Works

1. Video frames are captured using OpenCV.
2. Each frame is passed through the pre-trained YOLOv5 model for object detection.
3. Detected objects are drawn back onto the frame with bounding boxes and confidence scores.
4. Processed frames are displayed in real time.

## Setup

```bash
git clone https://github.com/tshende2004/real-time-object-detection-yolov5.git
cd real-time-object-detection-yolov5
pip install -r requirements.txt
python detect.py --source 0   # 0 for webcam, or path to a video file
```

## Results

- Stable real-time performance at 20+ FPS
- Reliable detection across varied lighting and motion conditions

## Future Improvements

- Fine-tune on a custom dataset for domain-specific object classes
- Add object tracking across frames (e.g., DeepSORT)
- Deploy as a web app using Streamlit or FastAPI for easier demoing

## Author

**Tejashree Shende** — [LinkedIn](https://www.linkedin.com/in/tejashree-shende-696b45312) · shendetejashree22@gmail.com
