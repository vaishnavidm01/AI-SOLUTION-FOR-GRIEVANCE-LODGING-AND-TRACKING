from flask import Flask, render_template, request
from flask_cors import CORS
import uuid

from database.db import init_db, insert_grievance, get_connection

app = Flask(__name__)
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

        category = request.form.get("category")
        description = request.form.get("description")
        location = request.form.get("location")

        image = request.files.get("image")

        # Generate unique grievance ID
        grievance_id = "GRV-" + str(uuid.uuid4())[:8].upper()

        # Get image filename
        image_filename = None

        if image and image.filename:
            image_filename = image.filename

        # Save grievance in database
        insert_grievance(
            grievance_id,
            category,
            description,
            location,
            image_filename
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