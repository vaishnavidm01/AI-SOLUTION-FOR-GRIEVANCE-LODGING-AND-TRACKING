
import os
from ai.pothole_detection import detect_potholes

image_path = os.path.join("uploads", "GRV-A14B20AC.jpg")

result = detect_potholes(image_path)

print(result)
