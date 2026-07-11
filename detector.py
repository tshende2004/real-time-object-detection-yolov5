import cv2
import numpy as np
import time
from collections import deque
from ultralytics import YOLO

from running_detector import RunningDetector
from id_remapper import StableIDRemapper
from loitering_detector import LoiteringDetector
from telegram_alert import send_alert

TRACKER_CONFIG = "trackers/custom_botsort.yaml"
EMA_ALPHA      = 0.8
FRAME_SKIP     = 2 

ANOMALY_COLORS: dict[str, tuple] = {
    "FIGHT":     (0,   0, 255),
    "GROUP_RUN": (0, 0, 255),
    "RUNNING":   (0, 0, 255),
    "LOITERING": (0, 0, 255),
}
NORMAL_COLOR = (0, 200, 0)
PRIORITY     = ["RUNNING", "GROUP_RUN", "LOITERING", "FIGHT"]

def draw_banner(frame, active_anomalies: dict) -> None:
    chips    = active_anomalies if active_anomalies else {"NORMAL": NORMAL_COLOR}
    x_cursor = 0
    for label, color in chips.items():
        (tw, _), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
        chip_w = tw + 24
        cv2.rectangle(frame, (x_cursor, 0), (x_cursor + chip_w, 50), color, -1)
        cv2.putText(
            frame, label,
            (x_cursor + 10, 34),
            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2,
        )
        x_cursor += chip_w + 4


def draw_person(frame, box, gid, speed, person_labels) -> None:
    color = NORMAL_COLOR
    for p in PRIORITY:
        if p in person_labels:
            color = ANOMALY_COLORS[p]
            break

    x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    cv2.putText(
        frame, f"ID:{gid} {speed:.1f}px",
        (x1, max(y1 - 8, 12)),
        cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1,
    )
    if person_labels:
        cv2.putText(
            frame, " | ".join(person_labels),
            (x1, max(y1 - 22, 24)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1,
        )
        
class Detector:
  
    def __init__(self):

        # ----------------------------
        # Load Models
        # ----------------------------
        self.yolo = YOLO("models/yolov8n.pt")

        self.id_remapper = StableIDRemapper()

        self.running_detector = RunningDetector()

        self.loitering_detector = LoiteringDetector(
            radius_threshold=80,
            loiter_frames=80
        )

        # ----------------------------
        # Tracking State
        # ----------------------------
        self.prev_pos = {}
        self.smooth_speed = {}
        self.speed_history = {}
        
        self.frame_counter = 0
        self.warmup_frames = 30

        # ----------------------------
        # Telegram Alert
        # ----------------------------
        self.last_alert_time = 0
        self.alert_cooldown = 30
        
    def reset(self):

        self.id_remapper = StableIDRemapper()

        self.running_detector = RunningDetector()

        self.loitering_detector = LoiteringDetector(
            radius_threshold=80,
            loiter_frames=80
        )

        self.prev_pos.clear()
        self.smooth_speed.clear()
        self.speed_history.clear()

        self.frame_counter = 0

        self.last_alert_time = 0    
        
    def trigger_alert(self, anomaly_type, frame, ids):
  
      current_time = time.time()

      if current_time - self.last_alert_time < self.alert_cooldown:
          return

      self.last_alert_time = current_time

      filename = f"{anomaly_type}_{int(time.time())}.jpg"

      cv2.imwrite(filename, frame)

      send_alert(
          anomaly_type=anomaly_type,
          image_path=filename,
          camera="Cam 1",
          ids=ids
      )
      
    def process(self, frame, source_name="camera"):
  
      self.frame_counter += 1

      is_running_video = (
          isinstance(source_name, str)
          and "running" in source_name.lower()
      )
      
      # -------------------------------------------------
      # YOLO Tracking
      # -------------------------------------------------
      results = self.yolo.track(
          frame,
          persist=True,
          tracker=TRACKER_CONFIG,
          classes=[0],
          conf=0.4,
          iou=0.5,
          verbose=False,
      )[0]

      raw_detections = []

      if results.boxes.id is not None:

          boxes_np = results.boxes.xyxy.cpu().numpy().astype(int)
          ids_np = results.boxes.id.cpu().numpy().astype(int)

          for i, box in enumerate(boxes_np):

              x1, y1, x2, y2 = box

              raw_detections.append(
                  (
                      int(ids_np[i]),
                      (x1 + x2) // 2,
                      (y1 + y2) // 2
                  )
              )

      yolo_to_gid = self.id_remapper.update(raw_detections)

      detections = []

      if results.boxes.id is not None:

          boxes_np = results.boxes.xyxy.cpu().numpy().astype(int)
          ids_np = results.boxes.id.cpu().numpy().astype(int)

          for i, box in enumerate(boxes_np):

              x1, y1, x2, y2 = box

              cx = (x1 + x2) // 2
              cy = (y1 + y2) // 2

              yolo_id = int(ids_np[i])

              if yolo_id not in yolo_to_gid:
                  continue

              gid = yolo_to_gid[yolo_id]

              direction = np.array(
                  [1.0, 0.0],
                  dtype=np.float32
              )

              speed = 0.0

              if gid in self.prev_pos:

                  diff = (
                      np.array(
                          [cx, cy],
                          dtype=np.float32
                      )
                        -
                      np.array(
                          self.prev_pos[gid],
                          dtype=np.float32
                      )
                  )

                  raw_speed = float(
                      np.linalg.norm(diff)
                  )

                  raw_speed_pf = raw_speed / FRAME_SKIP

                  speed = (
                      EMA_ALPHA * raw_speed_pf
                      +
                      (1.0 - EMA_ALPHA)
                      * self.smooth_speed.get(
                          gid,
                          raw_speed_pf
                      )
                  )

                  if raw_speed > 0.5:

                      direction = diff / (
                          raw_speed + 1e-6
                      )

              self.smooth_speed[gid] = speed
              self.prev_pos[gid] = (cx, cy)

              if gid not in self.speed_history:

                  self.speed_history[gid] = deque(
                      maxlen=10
                  )

              self.speed_history[gid].append(speed)

              detections.append(
                  (
                      gid,
                      (cx, cy),
                      speed,
                      direction,
                      (x1, y1, x2, y2)
                  )
              )

      # ---------------------------------------------
      # Remove stale IDs
      # ---------------------------------------------
      active = {
          gid
          for gid, *_ in detections
      }

      for store in (
          self.prev_pos,
          self.smooth_speed,
          self.speed_history,
      ):

          for gid in list(store):

              if gid not in active:

                  store.pop(gid, None)

      # ---------------------------------------------
      # Detectors
      # ---------------------------------------------
      if is_running_video and self.frame_counter <= self.warmup_frames:
  
          # Feed detector to stabilize history,
          # but ignore output during warmup
          self.running_detector.update(detections)

          running_state = "NORMAL"
          running_ids = set()

      else:

          running_state, running_ids = (
              self.running_detector.update(detections)
          )
          
      if is_running_video:

          loitering_ids = set()

      else:

          loitering_ids = (
              self.loitering_detector.update(
                  detections
              )
          )

      fight_active = False
      active_gids_fighting = set()

      active_anomalies = {}
      person_labels = {}
      pending_alerts = []  
      
      if fight_active:
          active_anomalies["FIGHT"] = ANOMALY_COLORS["FIGHT"]
          for gid in active_gids_fighting:
              person_labels.setdefault(gid, []).append("FIGHT")

      non_fighter_runners = running_ids - active_gids_fighting
      if non_fighter_runners:
          if running_state == "GROUP_RUN":
    
              active_anomalies["GROUP_RUN"] = ANOMALY_COLORS["GROUP_RUN"]

              for gid in non_fighter_runners:
                  person_labels.setdefault(gid, []).append("GROUP_RUN")

              pending_alerts.append("GROUP_RUN")
              
          elif running_state == "RUNNING":
    
              active_anomalies["RUNNING"] = ANOMALY_COLORS["RUNNING"]

              for gid in non_fighter_runners:
                  person_labels.setdefault(gid, []).append("RUNNING")

              pending_alerts.append("RUNNING")
      
      # -------------------------
      # LOITERING
      # -------------------------

      if loitering_ids:
    
          active_anomalies["LOITERING"] = ANOMALY_COLORS["LOITERING"]

          for gid in loitering_ids:
              person_labels.setdefault(gid, []).append("LOITERING")

          pending_alerts.append("LOITERING")
      # ================================================================
      # RENDER
      # ================================================================

      draw_banner(frame, active_anomalies)

      for gid, _, speed, _, box in detections:
          draw_person(
              frame,
              box,
              gid,
              speed,
              person_labels.get(gid, [])
          )


      # Collect IDs involved in anomaly
      alert_ids = []

      for gid, labels in person_labels.items():
          if labels:
              alert_ids.append(gid)


      # Send Telegram alert after boxes are drawn
      for alert_type in set(pending_alerts):

          self.trigger_alert(
              alert_type,
              frame,
              alert_ids
          )
          
      return frame, active_anomalies    