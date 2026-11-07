
from flask import Flask, render_template, request, redirect, url_for
import os
import sqlite3
import uuid
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024


def init_db():
    conn = sqlite3.connect("Database.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            genre TEXT NOT NULL,
            price INTEGER,
            poster TEXT
        )
    """)
    movie_columns = {
        column[1]
        for column in cursor.execute("PRAGMA table_info(movies)").fetchall()
    }
    if "poster" not in movie_columns:
        cursor.execute("ALTER TABLE movies ADD COLUMN poster TEXT")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ticket_bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            film TEXT NOT NULL,
            row_number INTEGER NOT NULL CHECK (row_number BETWEEN 1 AND 5),
            seat_number INTEGER NOT NULL CHECK (seat_number BETWEEN 1 AND 8),
            UNIQUE (film, row_number, seat_number)
        )
    """)

    conn.commit()
    conn.close()


def render_tickets(film, message=None, message_type=None, selected_seat=None, status=200):
    conn = sqlite3.connect("Database.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT row_number, seat_number FROM ticket_bookings WHERE film = ?",
        (film,)
    )
    booked_seats = {(row, seat) for row, seat in cursor.fetchall()}
    conn.close()

    return render_template(
        "tickets.html",
        film=film,
        booked_seats=booked_seats,
        rows=range(1, 6),
        seats_per_row=8,
        message=message,
        message_type=message_type,
        selected_seat=selected_seat
    ), status


@app.route("/")
def index():
    conn = sqlite3.connect("Database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT name, genre, poster FROM movies ORDER BY id")
    default_poster = url_for("static", filename="images/poster.jpg")
    films = [
        {
            **dict(movie),
            "poster": url_for(
                "static",
                filename=f"images/{movie['poster']}"
            ) if movie["poster"] else default_poster
        }
        for movie in cursor.fetchall()
    ]
    conn.close()

    return render_template("index.html", films=films)

@app.route("/movies")
def movies():
    conn = sqlite3.connect("Database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM movies")
    all_movies = cursor.fetchall()

    conn.close()
    return render_template("movies.html", movies=all_movies)

@app.route("/movies/<int:movie_id>/delete", methods=["POST"])
def delete_movie(movie_id):
    conn = sqlite3.connect("Database.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM movies WHERE id = ?", (movie_id,))

    conn.commit()
    conn.close()
    return redirect(url_for("movies"))

@app.route("/add_movies", methods=["GET", "POST"])
def add_movies():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        genre = request.form.get("genre", "").strip()
        if not name or not genre:
            return render_template(
                "add_movies.html",
                error="Вкажіть назву та жанр фільму."
            ), 400

        price = request.form.get("price") or None
        poster_file = request.files.get("poster")
        poster_filename = None

        if poster_file and poster_file.filename:
            extension = poster_file.filename.rsplit(".", maxsplit=1)[-1].lower()
            if "." not in poster_file.filename or extension not in {
                "jpg", "jpeg", "png", "webp", "gif"
            }:
                return render_template(
                    "add_movies.html",
                    error="Завантажте зображення у форматі JPG, PNG, WEBP або GIF."
                ), 400
            poster_filename = f"{uuid.uuid4().hex}.{secure_filename(extension)}"
            poster_file.save(
                os.path.join(app.static_folder, "images", poster_filename)
            )

        conn = sqlite3.connect("Database.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO movies (name, genre, price, poster) VALUES (?, ?, ?, ?)",
            (name, genre, price, poster_filename)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("movies"))

    return render_template("add_movies.html")


@app.errorhandler(413)
def file_too_large(_error):
    return render_template(
        "add_movies.html",
        error="Зображення завелике. Максимальний розмір — 5 МБ."
    ), 413


@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route("/contacts")
def contacts():
    return render_template("contacts.html")


@app.route("/tickets", methods=["GET", "POST"])
def tickets():
    if request.method == "POST":
        film = request.form.get("film", "").strip()
        seat = request.form.get("seat", "")

        try:
            row_number, seat_number = map(int, seat.split("-", maxsplit=1))
        except ValueError:
            row_number, seat_number = 0, 0

        if not film or not (1 <= row_number <= 5 and 1 <= seat_number <= 8):
            return render_tickets(
                film or "Фільм не вибрано",
                "Оберіть фільм і вільне місце.",
                "error",
                status=400
            )

        conn = sqlite3.connect("Database.db")
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO ticket_bookings (film, row_number, seat_number) VALUES (?, ?, ?)",
                (film, row_number, seat_number)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_tickets(
                film,
                "Це місце щойно зайняли. Оберіть інше.",
                "error",
                status=409
            )
        conn.close()
        return redirect(url_for(
            "tickets",
            film=film,
            row=row_number,
            seat=seat_number
        ))

    film = request.args.get("film", "").strip() or "Месники: Сходження Доктора Дума"
    row_number = request.args.get("row", type=int)
    seat_number = request.args.get("seat", type=int)
    selected_seat = None
    message = None
    if row_number is not None and seat_number is not None:
        selected_seat = (row_number, seat_number)
        message = f"Квиток заброньовано: ряд {row_number}, місце {seat_number}."
    return render_tickets(film, message, "success" if message else None, selected_seat)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
