from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
DB_PATH = "database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS personas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            edad INTEGER NOT NULL,
            genero TEXT NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_count():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM personas")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_all_data():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, edad, genero, fecha FROM personas ORDER BY id")
    rows = c.fetchall()
    conn.close()
    return rows

@app.route("/")
def index():
    count = get_count()
    return render_template("index.html", count=count, total=15)

@app.route("/agregar", methods=["POST"])
def agregar():
    edad = request.form.get("edad")
    genero = request.form.get("genero")

    if not edad or not genero:
        return redirect(url_for("index"))

    try:
        edad = int(edad)
        if edad < 0 or edad > 120:
            return redirect(url_for("index"))
    except ValueError:
        return redirect(url_for("index"))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO personas (edad, genero) VALUES (?, ?)", (edad, genero))
    conn.commit()
    conn.close()

    count = get_count()
    if count >= 15:
        return redirect(url_for("dashboard"))
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    rows = get_all_data()
    count = len(rows)
    return render_template("dashboard.html", rows=rows, count=count)

@app.route("/api/datos")
def api_datos():
    rows = get_all_data()
    data = [{"id": r[0], "edad": r[1], "genero": r[2], "fecha": r[3]} for r in rows]
    return jsonify(data)

@app.route("/api/stats")
def api_stats():
    rows = get_all_data()
    if not rows:
        return jsonify({})

    edades = [r[1] for r in rows]
    generos = [r[2] for r in rows]

    masculino = generos.count("Masculino")
    femenino = generos.count("Femenino")
    otro = generos.count("Otro")

    stats = {
        "total": len(rows),
        "edad_promedio": round(sum(edades) / len(edades), 1),
        "edad_min": min(edades),
        "edad_max": max(edades),
        "masculino": masculino,
        "femenino": femenino,
        "otro": otro,
        "edades": edades,
        "generos": generos
    }
    return jsonify(stats)

@app.route("/resetear", methods=["POST"])
def resetear():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM personas")
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

from flask import Response
import csv
import io

@app.route("/exportar-csv")
def exportar_csv():
    rows = get_all_data()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "edad", "genero", "fecha"])
    writer.writerows(rows)
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=datos.csv"}
    )

if __name__ == "__main__":
    init_db()
    app.run(debug=True)