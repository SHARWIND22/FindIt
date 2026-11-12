from flask import Flask, render_template, request, redirect, url_for
from database import init_db, get_db_connection
from pathlib import Path
from werkzeug.utils import secure_filename
from datetime import date
from flask import send_from_directory

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

UPLOAD_FOLDER.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

init_db()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    conn = get_db_connection()

    total_lost = conn.execute(
        "SELECT COUNT(*) FROM items WHERE item_type='lost' AND status='open'"
    ).fetchone()[0]

    total_found = conn.execute(
        "SELECT COUNT(*) FROM items WHERE item_type='found' AND status='open'"
    ).fetchone()[0]

    total_returned = conn.execute(
        "SELECT COUNT(*) FROM items WHERE status='returned'"
    ).fetchone()[0]

    recent_items = conn.execute(
        "SELECT * FROM items ORDER BY id DESC LIMIT 6"
    ).fetchall()

    conn.close()

    return render_template(
        "index.html",
        total_lost=total_lost,
        total_found=total_found,
        total_returned=total_returned,
        recent_items=recent_items
    )


@app.route("/report/<item_type>", methods=["GET", "POST"])
def report(item_type):

    if item_type not in ["lost", "found"]:
        return "Invalid report type", 404

    if request.method == "POST":

        item_name = request.form.get("item_name", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        contact = request.form.get("contact", "").strip()
        report_date = request.form.get("date_reported") or date.today().isoformat()

        if not all([item_name, category, description, location, contact]):
            return "Please fill in all required fields.", 400

        image = request.files.get("image")
        image_filename = None

        if image and image.filename:
            if not allowed_file(image.filename):
                return "Invalid image format.", 400

            safe_name = secure_filename(image.filename)
            image_filename = f"{date.today().strftime('%Y%m%d')}_{safe_name}"
            image.save(UPLOAD_FOLDER / image_filename)

        conn = get_db_connection()

        conn.execute("""
            INSERT INTO items
            (item_type, item_name, category, description,
             location, date_reported, image_filename, contact)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item_type, item_name, category, description,
            location, report_date, image_filename, contact
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("home"))

    return render_template("report.html", item_type=item_type)

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)