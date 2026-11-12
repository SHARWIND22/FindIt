from flask import (
    Flask, render_template, request, redirect,
    url_for, send_from_directory, session, flash
)
from database import init_db, get_db_connection
from pathlib import Path
from werkzeug.utils import secure_filename
from datetime import date
from matching import find_matches
from functools import wraps
import os
import hmac

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("Set the FLASK_SECRET_KEY environment variable.")

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")
if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    raise RuntimeError("Set ADMIN_USERNAME and ADMIN_PASSWORD environment variables.")

UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

init_db()

def migrate_student_columns():
    conn = get_db_connection()
    columns = [row["name"] for row in conn.execute("PRAGMA table_info(items)").fetchall()]
    for column in ("student_usn", "branch", "year"):
        if column not in columns:
            conn.execute(f"ALTER TABLE items ADD COLUMN {column} TEXT")
    conn.commit()
    conn.close()

migrate_student_columns()


def add_notification(item_id, message, recipient_role="admin", recipient_usn=None, link=None):
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO notifications
        (item_id, message, is_read, recipient_role, recipient_usn, link)
        VALUES (?, ?, 0, ?, ?, ?)
    """, (item_id, message, recipient_role, recipient_usn, link))
    conn.commit()
    conn.close()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Admin login required to perform this action.", "error")
            return redirect(url_for("admin_login", next=request.path))
        return function(*args, **kwargs)
    return wrapper

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
        sql += """ AND (item_name LIKE ? OR description LIKE ?
                   OR location LIKE ? OR student_usn LIKE ?)"""
        keyword = f"%{search_query}%"
        params.extend([keyword, keyword, keyword, keyword])
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
        "index.html", total_lost=total_lost, total_found=total_found,
        total_returned=total_returned, recent_items=recent_items,
        categories=categories, search_query=search_query,
        selected_type=selected_type, selected_category=selected_category
    )



@app.route("/report/<item_type>", methods=["GET", "POST"])
def report_item(item_type):
    if item_type not in ("lost", "found"):
        return "Invalid report type", 404

    if request.method == "POST":
        student_usn = request.form.get("student_usn", "").strip().upper()
        branch = request.form.get("branch", "").strip()
        year = request.form.get("year", "").strip()
        item_name = request.form.get("item_name", "").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()
        location = request.form.get("location", "").strip()
        date_reported = request.form.get("date_reported", "").strip() or date.today().isoformat()
        contact = request.form.get("contact", "").strip()

        if not all([student_usn, branch, year, item_name, category,
                    description, location, contact]):
            flash("Please complete all required fields.", "error")
            return render_template("report.html", item_type=item_type,
                                   today=date.today().isoformat())

        allowed_branches = ["AIML", "CSE", "ISE", "ECE", "EEE", "ME", "CIVIL"]
        allowed_years = ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        if branch not in allowed_branches or year not in allowed_years:
            flash("Please select a valid branch and year.", "error")
            return render_template("report.html", item_type=item_type,
                                   today=date.today().isoformat())

        image_filename = None
        image = request.files.get("image")
        if image and image.filename:
            if not allowed_file(image.filename):
                flash("Image must be PNG, JPG, JPEG or WEBP.", "error")
                return render_template("report.html", item_type=item_type,
                                       today=date.today().isoformat())
            safe_name = secure_filename(image.filename)
            unique_name = f"{item_type}_{date.today().strftime('%Y%m%d')}_{os.urandom(5).hex()}_{safe_name}"
            image.save(UPLOAD_FOLDER / unique_name)
            image_filename = unique_name

        conn = get_db_connection()
        cursor = conn.execute("""
            INSERT INTO items
            (item_type, item_name, category, description, location,
             date_reported, image_filename, contact, status,
             student_usn, branch, year)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, ?)
        """, (item_type, item_name, category, description, location,
              date_reported, image_filename, contact, student_usn, branch, year))
        item_id = cursor.lastrowid
        conn.commit()
        conn.close()

        add_notification(item_id, f"New {item_type} item reported: {item_name}",
                         "admin", link=f"/item/{item_id}")

        try:
            find_matches(item_id)
        except Exception as error:
            app.logger.exception("AI matching failed for item %s: %s", item_id, error)

        flash(f"{item_type.title()} item reported successfully!", "success")
        return redirect(url_for("item_details", item_id=item_id))

    return render_template("report.html", item_type=item_type,
                           today=date.today().isoformat())

@app.route("/item/<int:item_id>")
def item_details(item_id):
    conn = get_db_connection()
    item = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    existing_claim = None
    if item and not session.get("is_admin"):
        # This is a convenience check only; claims are not tied to a login session.
        existing_claim = None
    conn.close()
    if item is None:
        return render_template("item_details.html", item=None), 404
    return render_template(
        "item_details.html", item=item, is_admin=session.get("is_admin", False),
        existing_claim=existing_claim
    )

@app.route("/claim/<int:item_id>", methods=["GET", "POST"])
def claim_item(item_id):
    conn = get_db_connection()
    item = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if item is None:
        conn.close()
        return "Item not found", 404
    if item["item_type"] != "found":
        conn.close()
        return "Only found items can receive claim requests.", 400
    if item["status"] != "open":
        conn.close()
        flash("This item is no longer available for claiming.", "error")
        return redirect(url_for("item_details", item_id=item_id))

    if request.method == "POST":
        student_name = request.form.get("student_name", "").strip()
        student_usn = request.form.get("student_usn", "").strip().upper()
        branch = request.form.get("branch", "").strip()
        year = request.form.get("year", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        contact = f"Phone: {phone}" + (f" | Email: {email}" if email else "")
        ownership_proof = request.form.get("ownership_proof", "").strip()
        message = request.form.get("message", "").strip()

        if not all([student_name, student_usn, branch, year, phone, ownership_proof]):
            flash("Please complete all required fields.", "error")
            conn.close()
            return render_template("claim_request.html", item=item)

        if not all(ch.isdigit() or ch in "+() -" for ch in phone) or len(phone) < 7:
            flash("Please enter a valid phone number.", "error")
            conn.close()
            return render_template("claim_request.html", item=item)

        allowed_branches = ["AIML", "CSE", "ISE", "ECE", "EEE", "ME", "CIVIL"]
        allowed_years = ["1st Year", "2nd Year", "3rd Year", "4th Year"]
        if branch not in allowed_branches or year not in allowed_years:
            flash("Please select a valid branch and year.", "error")
            conn.close()
            return render_template("claim_request.html", item=item)

        duplicate = conn.execute("""
            SELECT id FROM claims
            WHERE item_id = ? AND student_usn = ? AND status = 'pending'
        """, (item_id, student_usn)).fetchone()
        if duplicate:
            conn.close()
            flash("You already have a pending claim for this item.", "error")
            return redirect(url_for("item_details", item_id=item_id))

        conn.execute("""
            INSERT INTO claims
            (item_id, student_name, student_usn, branch, year, contact,
             ownership_proof, message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (item_id, student_name, student_usn, branch, year, contact,
              ownership_proof, message))
        conn.commit()
        conn.close()
        add_notification(item_id,
                         f"New claim request from {student_name} ({student_usn}) for {item['item_name']}",
                         "admin", link="/admin/claims")
        add_notification(item_id,
                         f"Your claim request for {item['item_name']} was submitted and is pending review.",
                         "student", recipient_usn=student_usn, link="/notifications")
        flash("Claim request submitted. The admin will review your proof.", "success")
        return redirect(url_for("item_details", item_id=item_id))

    conn.close()
    return render_template("claim_request.html", item=item)

@app.route("/admin/claims")
@admin_required
def admin_claims():
    status_filter = request.args.get("status", "all")
    conn = get_db_connection()
    sql = """
        SELECT c.*, i.item_name, i.location, i.image_filename, i.status AS item_status
        FROM claims c JOIN items i ON c.item_id = i.id
    """
    params = []
    if status_filter in ("pending", "approved", "rejected"):
        sql += " WHERE c.status = ?"
        params.append(status_filter)
    sql += " ORDER BY CASE c.status WHEN 'pending' THEN 0 ELSE 1 END, c.created_at DESC"
    claims = conn.execute(sql, params).fetchall()
    conn.close()
    return render_template("admin_claims.html", claims=claims, status_filter=status_filter)

@app.route("/admin/claims/<int:claim_id>/<decision>", methods=["POST"])
@admin_required
def review_claim(claim_id, decision):
    if decision not in ("approved", "rejected"):
        return "Invalid decision", 400
    admin_note = request.form.get("admin_note", "").strip()
    conn = get_db_connection()
    claim = conn.execute("""
        SELECT c.*, i.status AS item_status, i.item_type
        FROM claims c JOIN items i ON c.item_id = i.id
        WHERE c.id = ?
    """, (claim_id,)).fetchone()
    if claim is None:
        conn.close()
        return "Claim not found", 404
    if claim["status"] != "pending":
        conn.close()
        flash("This claim has already been reviewed.", "error")
        return redirect(url_for("admin_claims"))
    if claim["item_type"] != "found" or claim["item_status"] != "open":
        conn.close()
        flash("This item is no longer available. Claim was not changed.", "error")
        return redirect(url_for("admin_claims"))

    conn.execute("""
        UPDATE claims SET status = ?, admin_note = ?, reviewed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (decision, admin_note, claim_id))
    student_usn = claim["student_usn"]
    item_id = claim["item_id"]
    item_row = conn.execute("SELECT item_name FROM items WHERE id = ?", (item_id,)).fetchone()
    item_name = item_row["item_name"] if item_row else "your item"
    conn.commit()
    conn.close()
    message = f"Your claim for {item_name} was {decision}."
    if admin_note:
        message += f" Admin note: {admin_note}"
    add_notification(item_id, message, "student", recipient_usn=student_usn,
                     link="/notifications")
    flash(f"Claim #{claim_id} {decision}. The item has NOT been marked returned.", "success")
    return redirect(url_for("admin_claims"))

@app.route("/notifications", methods=["GET", "POST"])
def notifications_page():
    is_admin = session.get("is_admin", False)
    if request.method == "POST":
        usn = request.form.get("student_usn", "").strip().upper()
        return redirect(url_for("notifications_page", usn=usn))

    student_usn = request.args.get("usn", "").strip().upper()
    conn = get_db_connection()
    if is_admin:
        notifications = conn.execute("""
            SELECT n.*, i.item_name FROM notifications n
            LEFT JOIN items i ON n.item_id = i.id
            WHERE n.recipient_role = 'admin'
            ORDER BY n.created_at DESC LIMIT 100
        """).fetchall()
    elif student_usn:
        notifications = conn.execute("""
            SELECT n.*, i.item_name FROM notifications n
            LEFT JOIN items i ON n.item_id = i.id
            WHERE n.recipient_role = 'student' AND n.recipient_usn = ?
            ORDER BY n.created_at DESC LIMIT 100
        """, (student_usn,)).fetchall()
    else:
        notifications = []
    conn.close()
    return render_template("notifications.html", notifications=notifications,
                           is_admin=is_admin, student_usn=student_usn)

@app.route("/notifications/read/<int:notification_id>", methods=["POST"])
def mark_notification_read(notification_id):
    is_admin = session.get("is_admin", False)
    student_usn = request.form.get("student_usn", "").strip().upper()
    conn = get_db_connection()
    if is_admin:
        conn.execute("UPDATE notifications SET is_read=1 WHERE id=? AND recipient_role='admin'",
                     (notification_id,))
        conn.commit()
        conn.close()
        return redirect(url_for("notifications_page"))
    if student_usn:
        conn.execute("""UPDATE notifications SET is_read=1
                        WHERE id=? AND recipient_role='student' AND recipient_usn=?""",
                     (notification_id, student_usn))
        conn.commit()
    conn.close()
    return redirect(url_for("notifications_page", usn=student_usn) if student_usn
                    else url_for("notifications_page"))

@app.route("/matches")
def matches_page():
    conn = get_db_connection()
    matches = conn.execute("""
        SELECT
            m.id AS match_id, m.similarity_score, m.explanation,
            m.status AS match_status,
            l.item_name AS lost_name, l.description AS lost_description,
            l.location AS lost_location, l.image_filename AS lost_image,
            l.contact AS lost_contact, l.student_usn AS lost_usn,
            l.branch AS lost_branch, l.year AS lost_year,
            f.item_name AS found_name, f.description AS found_description,
            f.location AS found_location, f.image_filename AS found_image,
            f.contact AS found_contact, f.student_usn AS found_usn,
            f.branch AS found_branch, f.year AS found_year
        FROM matches m
        JOIN items l ON m.lost_item_id = l.id
        JOIN items f ON m.found_item_id = f.id
        ORDER BY m.similarity_score DESC
    """).fetchall()
    conn.close()
    return render_template("matches.html", matches=matches,
                           is_admin=session.get("is_admin", False))

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("is_admin"):
        return redirect(url_for("matches_page"))
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if (hmac.compare_digest(username, ADMIN_USERNAME)
                and hmac.compare_digest(password, ADMIN_PASSWORD)):
            session.clear()
            session["is_admin"] = True
            flash("Admin login successful.", "success")
            next_page = request.args.get("next", "")
            if next_page == url_for("matches_page") or next_page.startswith(
                ("/mark-returned/", "/admin/claims", "/notifications")
            ):
                return redirect(next_page)
            return redirect(url_for("admin_claims"))
        flash("Invalid admin username or password.", "error")
    return render_template("admin_login.html")

@app.route("/admin/logout")
@admin_required
def admin_logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("matches_page"))

@app.route("/mark-returned/<int:match_id>", methods=["POST"])
@admin_required
def mark_returned(match_id):
    conn = get_db_connection()
    match = conn.execute(
        "SELECT lost_item_id, found_item_id FROM matches WHERE id = ?", (match_id,)
    ).fetchone()
    if match is None:
        conn.close()
        return "Match not found", 404
    conn.execute("UPDATE items SET status = 'returned' WHERE id IN (?, ?)",
                 (match["lost_item_id"], match["found_item_id"]))
    conn.execute("UPDATE matches SET status = 'returned' WHERE id = ?", (match_id,))
    conn.commit()
    conn.close()
    flash("Item successfully marked as returned.", "success")
    return redirect(url_for("matches_page"))

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == "__main__":
    app.run(debug=True)
