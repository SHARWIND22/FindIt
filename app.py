from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from database import init_db, get_db_connection
from pathlib import Path
from werkzeug.utils import secure_filename
from datetime import date
from matching import find_matches

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
        "SELECT COUNT(*) FROM items WHERE item_type='lost' AND status='returned'"
    ).fetchone()[0]

    search_query = request.args.get("search", "").strip()
    selected_type = request.args.get("type", "").strip()
    selected_category = request.args.get("category", "").strip()

    sql = "SELECT * FROM items WHERE 1=1"
    params = []

    if search_query:
        sql += """
            AND (
                item_name LIKE ?
                OR description LIKE ?
                OR location LIKE ?
            )
        """
        keyword = f"%{search_query}%"
        params.extend([keyword, keyword, keyword])

    if selected_type in ["lost", "found"]:
        sql += " AND item_type = ?"
        params.append(selected_type)

    if selected_category:
        sql += " AND category = ?"
        params.append(selected_category)

    sql += " ORDER BY id DESC LIMIT 50"

    recent_items = conn.execute(sql, params).fetchall()

    categories = conn.execute(
        "SELECT DISTINCT category FROM items ORDER BY category"
    ).fetchall()

    conn.close()

    return render_template(
        "index.html",
        total_lost=total_lost,
        total_found=total_found,
        total_returned=total_returned,
        recent_items=recent_items,
        categories=categories,
        search_query=search_query,
        selected_type=selected_type,
        selected_category=selected_category
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

        cursor = conn.execute("""
            INSERT INTO items
            (item_type, item_name, category, description,
             location, date_reported, image_filename, contact)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            item_type, item_name, category, description,
            location, report_date, image_filename, contact
        ))

        item_id = cursor.lastrowid

        conn.commit()
        conn.close()

        matches = find_matches(item_id)

        print("AI Matching Results:", matches)

        return redirect(url_for("home"))

    return render_template("report.html", item_type=item_type)


@app.route("/matches")
def matches_page():
    conn = get_db_connection()

    matches = conn.execute("""
        SELECT
            m.id AS match_id,
            m.similarity_score,
            m.explanation,
            m.status AS match_status,
            l.item_name AS lost_name,
            l.description AS lost_description,
            l.location AS lost_location,
            l.image_filename AS lost_image,
            l.contact AS lost_contact,
            f.item_name AS found_name,
            f.description AS found_description,
            f.location AS found_location,
            f.image_filename AS found_image,
            f.contact AS found_contact
        FROM matches m
        JOIN items l ON m.lost_item_id = l.id
        JOIN items f ON m.found_item_id = f.id
        ORDER BY m.similarity_score DESC
    """).fetchall()

    conn.close()

    return render_template("matches.html", matches=matches)


@app.route("/mark-returned/<int:match_id>", methods=["POST"])
def mark_returned(match_id):
    conn = get_db_connection()

    match = conn.execute(
        "SELECT lost_item_id, found_item_id FROM matches WHERE id = ?",
        (match_id,)
    ).fetchone()

    if match is None:
        conn.close()
        return "Match not found", 404

    conn.execute("""
        UPDATE items
        SET status = 'returned'
        WHERE id IN (?, ?)
    """, (match["lost_item_id"], match["found_item_id"]))

    conn.execute("""
        UPDATE matches
        SET status = 'returned'
        WHERE id = ?
    """, (match_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("matches_page"))


@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


if __name__ == "__main__":
    app.run(debug=True)