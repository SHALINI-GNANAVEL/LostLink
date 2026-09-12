from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os

from database import get_db_connection, initialize_database


app = Flask(__name__)


# =========================
# UPLOAD SETTINGS
# =========================

UPLOAD_FOLDER = "static/uploads"

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# =========================
# CHECK FILE TYPE
# =========================

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# =========================
# HOME PAGE
# =========================

@app.route("/")
def home():

    search = request.args.get("search", "")
    report_type = request.args.get("report_type", "")
    status = request.args.get("status", "")

    connection = get_db_connection()

    query = "SELECT * FROM items WHERE 1=1"

    parameters = []


    # =========================
    # SEARCH
    # =========================

    if search:

        query += """
            AND (
                item_name LIKE ?
                OR location LIKE ?
                OR description LIKE ?
            )
        """

        search_value = f"%{search}%"

        parameters.extend([
            search_value,
            search_value,
            search_value
        ])


    # =========================
    # REPORT TYPE FILTER
    # =========================

    if report_type:

        query += " AND report_type = ?"

        parameters.append(report_type)


    # =========================
    # STATUS FILTER
    # =========================

    if status:

        query += " AND status = ?"

        parameters.append(status)


    # Latest reports first

    query += " ORDER BY id DESC"


    items = connection.execute(
        query,
        parameters
    ).fetchall()


    # =========================
    # DASHBOARD STATISTICS
    # =========================

    total_lost = connection.execute("""
        SELECT COUNT(*)
        FROM items
        WHERE report_type = 'Lost'
    """).fetchone()[0]


    total_found = connection.execute("""
        SELECT COUNT(*)
        FROM items
        WHERE report_type = 'Found'
    """).fetchone()[0]


    total_returned = connection.execute("""
        SELECT COUNT(*)
        FROM items
        WHERE status = 'Returned'
    """).fetchone()[0]


    connection.close()


    return render_template(
        "index.html",
        items=items,
        search=search,
        report_type=report_type,
        status=status,
        total_lost=total_lost,
        total_found=total_found,
        total_returned=total_returned
    )


# =========================
# ADD ITEM
# =========================

@app.route("/add", methods=["POST"])
def add_item():

    item_name = request.form["item_name"]

    category = request.form["category"]

    description = request.form["description"]

    location = request.form["location"]

    report_type = request.form["report_type"]

    date_reported = request.form["date_reported"]

    contact = request.form["contact"]


    # =========================
    # IMAGE UPLOAD
    # =========================

    image = request.files.get("image")

    image_filename = None


    if image and image.filename:

        if allowed_file(image.filename):

            filename = secure_filename(image.filename)

            image_filename = filename

            image.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    filename
                )
            )


    # =========================
    # SAVE TO DATABASE
    # =========================

    connection = get_db_connection()


    connection.execute("""
        INSERT INTO items
        (
            item_name,
            category,
            description,
            location,
            report_type,
            date_reported,
            image,
            contact
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item_name,
        category,
        description,
        location,
        report_type,
        date_reported,
        image_filename,
        contact
    ))


    connection.commit()

    connection.close()


    return redirect(url_for("home"))


# =========================
# MARK AS RETURNED
# =========================

@app.route("/return/<int:item_id>")
def mark_returned(item_id):

    connection = get_db_connection()


    connection.execute("""
        UPDATE items
        SET status = 'Returned'
        WHERE id = ?
    """, (item_id,))


    connection.commit()

    connection.close()


    return redirect(url_for("home"))


# =========================
# FIND POTENTIAL MATCHES
# =========================

@app.route("/matches/<int:item_id>")
def find_matches(item_id):

    connection = get_db_connection()


    # Get selected item

    item = connection.execute("""
        SELECT *
        FROM items
        WHERE id = ?
    """, (item_id,)).fetchone()


    # Item does not exist

    if not item:

        connection.close()

        return redirect(url_for("home"))


    # =========================
    # FIND MATCHING FOUND ITEMS
    # =========================

    matches = connection.execute("""
        SELECT *
        FROM items
        WHERE report_type = 'Found'
        AND category = ?
        AND status = 'Active'
        AND id != ?
        ORDER BY id DESC
    """, (
        item["category"],
        item["id"]
    )).fetchall()


    connection.close()


    return render_template(
        "matches.html",
        item=item,
        matches=matches
    )


# =========================
# START APPLICATION
# =========================

if __name__ == "__main__":

    initialize_database()

    app.run(debug=True)