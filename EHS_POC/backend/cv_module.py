"""
Computer Vision Module - EHS Safety Detection
Pipeline:
1. YOLOv8 COCO → person detection
2. PPE YOLO custom model → PPE detection
3. Associate PPE ↔ persons using IoU
4. Detect missing PPE per person
"""

import cv2
import numpy as np
import base64
import logging
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class SafetyDetector:
    def __init__(
        self,
        person_model_path: str = "models/yolov8s.pt",
        ppe_model_path: str = "models/ppe_detection.pt",
        confidence: float = 0.25
    ):
        self.person_model_path = person_model_path
        self.ppe_model_path = ppe_model_path
        self.confidence = confidence

        self.person_model = None
        self.ppe_model = None

        # REQUIRED PPE
        self.required_ppe = {
            "helmet",
            "vest",
            "gloves",
            "mask",
            "goggles",
            "safety_shoe"
        }

        self._load_models()

    # LOAD MODELS
    def _load_models(self):
        try:
            self.person_model = YOLO(self.person_model_path)
            logger.info("Person model loaded")

        except Exception as e:
            logger.error(f"Person model load failed: {e}")
            self.person_model = None

        try:
            self.ppe_model = YOLO(self.ppe_model_path)
            logger.info("PPE model loaded")

        except Exception as e:
            logger.error(f"PPE model load failed: {e}")
            self.ppe_model = None

    # IMAGE PREPROCESSING
    def preprocess_image(self, img):
        denoised = cv2.bilateralFilter(img, d=9, sigmaColor=75, sigmaSpace=75)
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)

        enhanced_lab = cv2.merge((cl, a, b))
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)

        kernel = np.array([
            [0, -1, 0],
            [-1, 5, -1],
            [0, -1, 0]
        ])

        sharpened = cv2.filter2D(enhanced, -1, kernel)
        return sharpened

    # IMAGE DECODING
    def decode_image(self, image_data):
        if isinstance(image_data, str):
            if "," in image_data:
                image_data = image_data.split(",")[1]
            img_bytes = base64.b64decode(image_data)
        else:
            img_bytes = image_data

        img_array = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Invalid image")

        return img

    # =========================
    # FIXED PERSON DETECTION (DEDUP ADDED)
    # =========================
    def detect_persons(self, img):
        detections = []

        if self.person_model is None:
            return detections

        results = self.person_model(
            img,
            conf=self.confidence,
            iou=0.5,
            verbose=False
        )

        temp = []

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = r.names[cls_id]

                if label.lower() != "person":
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])

                temp.append({
                    "class_id": cls_id,
                    "label": label,
                    "confidence": round(conf, 3),
                    "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "center": {"x": (x1 + x2) // 2, "y": (y1 + y2) // 2},
                    "area": (x2 - x1) * (y2 - y1)
                })

        # IoU based deduplication
        def iou(a, b):
            xA = max(a["x1"], b["x1"])
            yA = max(a["y1"], b["y1"])
            xB = min(a["x2"], b["x2"])
            yB = min(a["y2"], b["y2"])
            inter = max(0, xB - xA) * max(0, yB - yA)
            areaA = (a["x2"] - a["x1"]) * (a["y2"] - a["y1"])
            areaB = (b["x2"] - b["x1"]) * (b["y2"] - b["y1"])
            union = areaA + areaB - inter + 1e-6
            return inter / union

        filtered = []

        for det in temp:
            duplicate = False

            for f in filtered:
                if iou(det["bbox"], f["bbox"]) > 0.7:
                    duplicate = True
                    break

            if not duplicate:
                filtered.append(det)

        return filtered

    # PPE DETECTION
    def detect_ppe(self, img):
        detections = []

        if self.ppe_model is None:
            return detections

        processed_img = self.preprocess_image(img)

        results = self.ppe_model.predict(
            source=processed_img,
            conf=0.20,
            imgsz=960,
            augment=True,
            verbose=False
        )

        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                label = r.names[cls_id]

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])

                detections.append({
                    "class_id": cls_id,
                    "label": label,
                    "confidence": round(conf, 3),
                    "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "center": {"x": (x1 + x2) // 2, "y": (y1 + y2) // 2}
                })

        return detections

    # IoU
    def iou(self, boxA, boxB):
        xA = max(boxA["x1"], boxB["x1"])
        yA = max(boxA["y1"], boxB["y1"])
        xB = min(boxA["x2"], boxB["x2"])
        yB = min(boxA["y2"], boxB["y2"])

        inter = max(0, xB - xA) * max(0, yB - yA)

        areaA = ((boxA["x2"] - boxA["x1"]) * (boxA["y2"] - boxA["y1"]))
        areaB = ((boxB["x2"] - boxB["x1"]) * (boxB["y2"] - boxB["y1"]))

        union = areaA + areaB - inter + 1e-6

        return inter / union

    # PPE ANALYSIS
    def analyze_ppe(self, persons, ppe_detections):
        results = []

        for person in persons:
            pbox = person["bbox"]
            detected_items = set()
            violations = []

            for ppe in ppe_detections:
                label = ppe["label"].lower()
                box = ppe["bbox"]

                overlap = self.iou(pbox, box)
                if overlap < 0.05:
                    continue

                detected_items.add(label)

            missing_items = []

            for item in self.required_ppe:
                if item not in detected_items:
                    missing_items.append(item)

            violations.extend(missing_items)

            results.append({
                "person_bbox": pbox,
                "hard_hat_detected": "helmet" in detected_items,
                "safety_vest_detected": "vest" in detected_items,
                "ppe_compliant": len(missing_items) == 0,
                "violations": violations
            })

        all_missing_ppe = []
        for r in results:
            all_missing_ppe.extend(r["violations"])

        all_missing_ppe = list(set(all_missing_ppe))

        return {
            "persons_detected": len(persons),
            "ppe_status": results,
            "compliant_count": sum(1 for r in results if r["ppe_compliant"]),
            "violation_count": sum(1 for r in results if not r["ppe_compliant"]),
            "missing_ppe": all_missing_ppe
        }

    # HAZARDS
    def detect_hazards(self, img, detections, ppe_analysis):
        hazards = []

        if ppe_analysis["violation_count"] > 0:
            hazards.append({
                "type": "ppe_violation",
                "description": f"{ppe_analysis['violation_count']} violations detected",
                "confidence": 0.90,
                "severity": "HIGH"
            })

        return hazards

    # ANNOTATE IMAGE
    def annotate_image(self, img, detections, ppe_status):
        annotated = img.copy()

        for d in detections:
            b = d["bbox"]
            label = d["label"]
            conf = d["confidence"]

            color = (255, 165, 0) if label.lower() == "person" else (0, 255, 0)

            cv2.rectangle(annotated, (b["x1"], b["y1"]), (b["x2"], b["y2"]), color, 2)
            cv2.putText(
                annotated,
                f"{label} {conf:.2f}",
                (b["x1"], b["y1"] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                color,
                2
            )

        for p in ppe_status["ppe_status"]:
            if not p["ppe_compliant"]:
                b = p["person_bbox"]

                violations_text = ", ".join(set(p["violations"]))

                cv2.rectangle(annotated, (b["x1"], b["y1"]), (b["x2"], b["y2"]), (0, 0, 255), 3)

                cv2.putText(
                    annotated,
                    f"Missing: {violations_text}",
                    (b["x1"], b["y1"] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2
                )

        _, buffer = cv2.imencode(".jpg", annotated)
        return base64.b64encode(buffer).decode()

    # MAIN PIPELINE
    def process_image(self, image_data):
        img = self.decode_image(image_data)

        persons = self.detect_persons(img)
        ppe = self.detect_ppe(img)

        ppe_analysis = self.analyze_ppe(persons, ppe)
        hazards = self.detect_hazards(img, persons, ppe_analysis)

        annotated = self.annotate_image(img, persons + ppe, ppe_analysis)
        h, w = img.shape[:2]

        return {
            "image_dimensions": {"width": int(w), "height": int(h)},
            "total_detections": len(persons) + len(ppe),
            "detections": persons + ppe,
            "ppe_analysis": ppe_analysis,
            "hazards_detected": hazards,
            "annotated_image": annotated,
            "summary": {
                "persons_in_frame": len(persons),
                "ppe_violations": ppe_analysis["violation_count"],
                "hazard_count": len(hazards),
                "missing_ppe": ppe_analysis["missing_ppe"],
                "requires_review": (
                    ppe_analysis["violation_count"] > 0
                    or len(hazards) > 0
                )
            }
        }