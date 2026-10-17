
import os
import cv2
from ai.image_processing import process_grievance_image

image_path = os.path.join(
    "uploads", "GRV-E98F1258.jpg"
)

processed_image = process_grievance_image(image_path)

if processed_image is not None:
    print("Image processing successful!")
    print("Processed image size:", processed_image.shape)

    cv2.imwrite("uploads/processed_test.jpg", processed_image)
    print("Processed image saved successfully!")
else:
    print("Image not found or could not be read.")
