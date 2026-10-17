
from ultralytics import YOLO
import os

# Load a lightweight YOLO model.
# Note: this general model is for setup testing,
# not reliable pothole detection yet.
MODEL_NAME = "ai/models/best.pt"


def detect_potholes(image_path):
    if not os.path.exists(image_path):
        return {"success": False, "message": "Image not found"}

    try:
        model = YOLO(MODEL_NAME)
        results = model.predict(
            source=image_path,
            imgsz=640,
            verbose=False
        )

        detections = []

        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = result.names[class_id]

                if class_name.lower() == "pothole":
                    detections.append({
                        "label": class_name,
                        "confidence": float(box.conf[0])
                    })

        return {
            "success": True,
            "potholes_detected": len(detections),
            "detections": detections,
            "message": "Pothole detection completed successfully."
        }

    except Exception as error:
        return {"success": False, "message": str(error)}
