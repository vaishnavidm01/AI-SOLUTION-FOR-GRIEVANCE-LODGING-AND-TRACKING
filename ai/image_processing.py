
import cv2
import os


def process_grievance_image(image_path):
    if not os.path.exists(image_path):
        return None

    image = cv2.imread(image_path)

    if image is None:
        return None

    # Resize the image for consistent processing
    resized_image = cv2.resize(image, (640, 640))

    # Convert the image to grayscale
    grayscale_image = cv2.cvtColor(
        resized_image, cv2.COLOR_BGR2GRAY
    )

    # Reduce noise
    processed_image = cv2.GaussianBlur(
        grayscale_image, (5, 5), 0
    )

    return processed_image
