
from flask import (
    Flask,
    render_template,
    request,
    send_from_directory,
    redirect,
    url_for,
    session,
    abort
)

from flask_cors import CORS

import uuid
import joblib
import os
import sqlite3

from functools import wraps
from werkzeug.utils import secure_filename
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database.db import (
    init_db,
    insert_grievance,
    get_connection,
    create_user,
    get_user_by_email,
    get_user_by_id,
    get_user_grievances,
    get_all_grievances
)

from ai.severity_rules import predict_severity
from ai.department_routing import assign_department
from ai.image_processing import process_grievance_image
from ai.pothole_detection import detect_potholes

from ai.gps_cluster_service import (
    cluster_saved_grievances,
    get_cluster_summary
)


# =========================
# LOAD NLP MODEL
# =========================

nlp_model = joblib.load("ai/models/nlp_category_model.pkl")


# =========================
# FLASK CONFIGURATION
# =========================

app = Flask(__name__)

# Local development key.
# Set FLASK_SECRET_KEY to a private random value before deployment.
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "janseva-ai-local-development-key-change-before-deployment"
)

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("FLASK_HTTPS_ONLY", "").lower() == "true"
)

UPLOAD_FOLDER = os.path.join(app.root_path, "uploads")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

CORS(app)

# Initialize database
init_db()


# =========================
# FILE VALIDATION
# =========================

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# =========================
# AUTHENTICATION DECORATORS
# =========================

def login_required(view):

    @wraps(view)
    def wrapped_view(*args, **kwargs):

        user_id = session.get("user_id")

        if not user_id:
            return redirect(url_for("login"))

        user = get_user_by_id(user_id)

        if not user:
            session.clear()
            return redirect(url_for("login"))

        return view(*args, **kwargs)

    return wrapped_view


def role_required(required_role):

    def decorator(view):

        @wraps(view)
        def wrapped_view(*args, **kwargs):

            user_id = session.get("user_id")

            if not user_id:
                return redirect(url_for("login"))

            user = get_user_by_id(user_id)

            if not user:
                session.clear()
                return redirect(url_for("login"))

            if user["role"] != required_role:
                abort(403)

            return view(*args, **kwargs)

        return wrapped_view

    return decorator


# =========================
# HOME PAGE
# =========================

@app.route("/")
def home():

    return render_template("index.html")


# =========================
# CITIZEN REGISTRATION
# =========================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not full_name or not email or not password:
            return render_template(
                "register.html",
                error="Please fill in all required fields."
            ), 400

        if len(full_name) > 100 or len(email) > 254:
            return render_template(
                "register.html",
                error="Name or email is too long."
            ), 400

        if len(password) < 8:
            return render_template(
                "register.html",
                error="Password must contain at least 8 characters."
            ), 400

        if password != confirm_password:
            return render_template(
                "register.html",
                error="Passwords do not match."
            ), 400

        # Check whether email is already registered
        existing_user = get_user_by_email(email)

        if existing_user:
            return render_template(
                "register.html",
                error="This email address is already registered."
            ), 400

        # Hash password before database storage
        password_hash = generate_password_hash(password)

        try:

            # Public registration always creates a citizen.
            # The role is never accepted from the registration form.
            create_user(
                full_name,
                email,
                password_hash
            )

        except sqlite3.IntegrityError:

            return render_template(
                "register.html",
                error="This email address is already registered."
            ), 400

        return redirect(url_for("login"))

    return render_template("register.html")


# =========================
# USER LOGIN
# =========================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = get_user_by_email(email) if email else None

        if user and check_password_hash(
            user["password_hash"],
            password
        ):

            # Clear any previous session data
            session.clear()

            session["user_id"] = user["id"]
            session["role"] = user["role"]
            session["full_name"] = user["full_name"]

            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))

            return redirect(url_for("citizen_dashboard"))

        return render_template(
            "login.html",
            error="Invalid email address or password."
        ), 401

    return render_template("login.html")


# =========================
# USER LOGOUT
# =========================

@app.route("/logout")
@login_required
def logout():

    session.clear()

    return redirect(url_for("home"))
@app.route("/citizen-dashboard")
@role_required("citizen")
def citizen_dashboard():


    user = get_user_by_id(session["user_id"])

    return render_template(
        "citizen_dashboard.html",
        user=user
    )

@app.route("/my-grievances")
@role_required("citizen")
def my_grievances():

    grievances = get_user_grievances(session["user_id"])

    return render_template(
        "my_grievances.html",
        grievances=grievances
    )

# =========================
# LODGE GRIEVANCE
# =========================

@app.route("/lodge", methods=["GET", "POST"])
@role_required("citizen")
def lodge():

    if request.method == "POST":

        description = request.form.get("description")
        location = request.form.get("location")

        # Validate required fields
        if not description or not description.strip():
            return "Please enter a grievance description.", 400

        if not location or not location.strip():
            return "Please enter the grievance location.", 400

        description = description.strip()
        location = location.strip()

        latitude = request.form.get("latitude") or None
        longitude = request.form.get("longitude") or None

        try:

            latitude = float(latitude) if latitude is not None else None
            longitude = float(longitude) if longitude is not None else None

        except ValueError:

            latitude = None
            longitude = None

        # Validate GPS coordinate ranges
        if latitude is not None and longitude is not None:

            if not (-90 <= latitude <= 90):
                latitude = None
                longitude = None

            elif not (-180 <= longitude <= 180):
                latitude = None
                longitude = None

        else:

            latitude = None
            longitude = None

        # Predict complaint category using NLP model
        category = nlp_model.predict([description])[0]

        print("AI Predicted Category:", category)

        department = assign_department(category)

        print("Assigned Department:", department)

        # Estimate severity
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

        image_filename = None
        potholes_detected = 0
        detection_confidence = 0.0

        # Image upload and processing
        if image and image.filename:

            if not allowed_file(image.filename):
                return (
                    "Invalid image type. Please upload PNG, JPG, JPEG, or WEBP.",
                    400
                )

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

            # OpenCV preprocessing
            processed_image = process_grievance_image(image_path)

            if processed_image is None:

                os.remove(image_path)

                return "Uploaded file is not a valid or readable image.", 400

            print("OpenCV preprocessing successful!")

            # YOLO pothole detection
            pothole_result = detect_potholes(image_path)

            print("YOLO Pothole Detection:", pothole_result)

            if pothole_result.get("success"):

                potholes_detected = pothole_result.get(
                    "potholes_detected", 0
                )

                detections = pothole_result.get("detections", [])

                if detections:

                    detection_confidence = max(
                        item.get("confidence", 0.0)
                        for item in detections
                    )

                print("Potholes detected:", potholes_detected)
                print("Detection confidence:", detection_confidence)

            else:

                print(
                    "Pothole detection failed:",
                    pothole_result.get("message")
                )

        # Save grievance and associate it with the logged-in citizen
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
            longitude,
            user_id=session["user_id"]
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

        print("Citizen ID   :", session["user_id"])
        print("==============================\n")

        return render_template(
            "success.html",
            grievance_id=grievance_id
        )

    return render_template("lodge.html")


# =========================
# SERVE UPLOADED IMAGES
# =========================

@app.route("/uploads/<filename>")
@login_required
def uploaded_file(filename):

    user = get_user_by_id(session["user_id"])

    conn = get_connection()

    try:

        grievance = conn.execute(
            """
            SELECT user_id
            FROM grievances
            WHERE image_filename = ?
            """,
            (filename,)
        ).fetchone()

    finally:

        conn.close()

    if not grievance:
        abort(404)

    # Admin can view all uploaded grievance images.
    # Citizens can view only images belonging to their grievances.
    if (
        user["role"] != "admin"
        and grievance["user_id"] != session["user_id"]
    ):
        abort(403)

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename
    )


# =========================
# TRACK GRIEVANCE
# =========================


@app.route("/track", methods=["GET", "POST"])
@login_required
def track():

    # Open the tracking page
    if request.method == "GET":
        return render_template("track.html", grievance=None)

    grievance_id = request.form.get("grievance_id", "").strip()

    user = get_user_by_id(session["user_id"])

    conn = get_connection()

    try:

        if user["role"] == "admin":

            grievance = conn.execute(
                """
                SELECT *
                FROM grievances
                WHERE grievance_id = ?
                """,
                (grievance_id,)
            ).fetchone()

        else:

            grievance = conn.execute(
                """
                SELECT *
                FROM grievances
                WHERE grievance_id = ?
                  AND user_id = ?
                """,
                (grievance_id, session["user_id"])
            ).fetchone()

    finally:
        conn.close()

    if grievance:
        return render_template(
            "track.html",
            grievance=grievance
        )

    return render_template(
        "track.html",
        grievance=None,
        error="Grievance ID not found or you do not have permission to view it."
    )


# =========================
# ADMIN DASHBOARD
# =========================



@app.route("/admin-dashboard")
@role_required("admin")
def admin_dashboard():

    grievances = get_all_grievances()

    # Department-wise classification
    road_count = 0
    water_count = 0
    garbage_count = 0

    for grievance in grievances:

        department = (grievance.get("department") or "").lower()
        category = (grievance.get("category") or "").lower()

        if "road" in department or "road" in category or "mobility" in category:
            road_count += 1

        elif "water" in department or "water" in category:
            water_count += 1

        elif "waste" in department or "garbage" in department or "garbage" in category:
            garbage_count += 1

    # Severity statistics
    critical_count = sum(
        1 for g in grievances
        if (g.get("severity") or "").lower() == "critical"
    )

    # Status statistics
    resolved_count = sum(
        1 for g in grievances
        if (g.get("status") or "").lower() in
        ["resolved", "completed", "closed"]
    )

    pending_count = sum(
        1 for g in grievances
        if (g.get("status") or "").lower() not in
        ["resolved", "completed", "closed"]
    )

    return render_template(
        "admin_dashboard.html",
        grievances=grievances,
        total_grievances=len(grievances),
        road_count=road_count,
        water_count=water_count,
        garbage_count=garbage_count,
        critical_count=critical_count,
        pending_count=pending_count,
        resolved_count=resolved_count
    )

# =========================
# GPS MAP - ADMIN ONLY
# =========================

@app.route("/gps-map")
@role_required("admin")
def gps_map():

    return render_template("gps_map.html")


# =========================
# GPS GRIEVANCE API - ADMIN ONLY
# =========================

@app.route("/api/gps-grievances")
@role_required("admin")
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
