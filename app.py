from flask import Flask, render_template, request, send_from_directory
from flask_cors import CORS
import uuid
import joblib
import os
from werkzeug.utils import secure_filename
from database.db import init_db, insert_grievance, get_connection
from ai.severity_rules import predict_severity
from ai.department_routing import assign_department

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
        # Save grievance in database
        insert_grievance(
            grievance_id,
            category,
            description,
            location,
            image_filename,
            severity,
            department
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


# =========================
# RUN SERVER
# =========================

if __name__ == "__main__":
    app.run(debug=True)