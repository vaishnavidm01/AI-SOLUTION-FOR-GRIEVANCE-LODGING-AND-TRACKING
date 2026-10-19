from flask import Flask, render_template, request, send_from_directory
from flask_cors import CORS
import uuid
import joblib
import os
from werkzeug.utils import secure_filename
from database.db import init_db, insert_grievance, get_connection
from ai.severity_rules import predict_severity
from ai.department_routing import assign_department
from ai.image_processing import process_grievance_image
from ai.pothole_detection import detect_potholes
from ai.gps_cluster_service import (
    cluster_saved_grievances,
    get_cluster_summary
)

nlp_model = joblib.load("ai/models/nlp_category_model.pkl")
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )
app = Flask(__name__)
UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB
CORS(app)

# Initialize database
init_db()


# =========================
# HOME PAGE
# =========================

@app.route("/")
def home():
    return render_template("index.html")


# =========================
# LODGE GRIEVANCE
# =========================

@app.route("/lodge", methods=["GET", "POST"])
def lodge():

    if request.method == "POST":

        description = request.form.get("description")
        location = request.form.get("location")
        latitude = request.form.get("latitude") or None
        longitude = request.form.get("longitude") or None

        try:
            latitude = float(latitude) if latitude is not None else None
            longitude = float(longitude) if longitude is not None else None
        except ValueError:
            latitude = None
            longitude = None

        # Predict complaint category using NLP model

        # Predict complaint category using NLP model
        category = nlp_model.predict([description])[0]
        print("AI Predicted Category:", category)
        department = assign_department(category)
        print("Assigned Department:", department)

        # Estimate severity using rule-based logic
        image = request.files.get("image")
        has_photo = bool(image and image.filename)

        severity = predict_severity(
            description=description,
            category=category,
            has_photo=has_photo
        )

        print("Estimated Severity:", severity)



        # Generate unique grievance ID
        grievance_id = "GRV-" + str(uuid.uuid4())[:8].upper()

        # Get image filename
        # Save uploaded image with a safe, unique filename
        # Save uploaded image with validation
        image_filename = None
        potholes_detected = 0
        detection_confidence = 0.0

        if image and image.filename:
            if not allowed_file(image.filename):
                return "Invalid image type. Please upload PNG, JPG, JPEG, or WEBP.", 400

            original_filename = secure_filename(image.filename)

            if not original_filename:
                return "Invalid filename.", 400

            extension = os.path.splitext(original_filename)[1].lower()
            image_filename = f"{grievance_id}{extension}"

            image_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                image_filename
            )

            image.save(image_path)

            # OpenCV image preprocessing
            processed_image = process_grievance_image(image_path)

            if processed_image is not None:
                print("OpenCV preprocessing successful!")

            # YOLO pothole detection
            # YOLO pothole detection
            pothole_result = detect_potholes(image_path)
            print("YOLO Pothole Detection:", pothole_result)

            if pothole_result.get("success"):
                potholes_detected = pothole_result.get("potholes_detected", 0)

                detections = pothole_result.get("detections", [])

                if detections:
                    detection_confidence = max(
                        item.get("confidence", 0.0)
                        for item in detections
                    )

                print("Potholes detected:", potholes_detected)
                print("Detection confidence:", detection_confidence)
            else:
                print("Pothole detection failed:", pothole_result.get("message"))
        # Save grievance in database
        insert_grievance(
            grievance_id,
            category,
            description,
            location,
            image_filename,
            severity,
            department,
            potholes_detected,
            detection_confidence,
            latitude,
            longitude
        )

        print("\n==============================")
        print("NEW GRIEVANCE")
        print("==============================")
        print("Grievance ID :", grievance_id)
        print("Category     :", category)
        print("Description  :", description)
        print("Location     :", location)

        if image_filename:
            print("Image        :", image_filename)

        print("==============================\n")

        return render_template(
            "success.html",
            grievance_id=grievance_id
        )

    return render_template("lodge.html")


# =========================
# TRACK GRIEVANCE
# =========================
# =========================
# SERVE UPLOADED IMAGES
# =========================

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )

@app.route("/track", methods=["POST"])
def track():

    grievance_id = request.form.get("grievance_id")

    conn = get_connection()

    grievance = conn.execute(
        "SELECT * FROM grievances WHERE grievance_id = ?",
        (grievance_id,)
    ).fetchone()

    conn.close()

    if grievance:

        return render_template(
            "track.html",
            grievance=grievance
        )

    return render_template(
        "track.html",
        grievance=None,
        error="Grievance ID not found. Please check your ID."
    )

@app.route("/gps-map")
def gps_map():
    return render_template("gps_map.html")


@app.route("/api/gps-grievances")
def gps_grievances_api():
    grievances = cluster_saved_grievances()
    summary = get_cluster_summary()

    return {
        "total": summary["total_gps_grievances"],
        "clusters_found": summary["clusters_found"],
        "unclustered": summary["unclustered_grievances"],
        "grievances": grievances
    }


# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":
    app.run(debug=True)