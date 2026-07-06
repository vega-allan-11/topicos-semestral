import os
import sqlite3
from flask import Flask, request, jsonify

app = Flask(__name__)
DB = os.getenv("DB_PATH", "inventory.db")


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0,
                price REAL NOT NULL DEFAULT 0
            )
        """)


@app.route("/")
def index():
    return jsonify(
        service="inventory-manager",
        endpoints=["/health", "/products (GET, POST)", "/products/<id> (GET, PUT, DELETE)"],
    ), 200


@app.route("/health")
def health():
    return jsonify(status="ok"), 200


@app.route("/products", methods=["GET"])
def list_products():
    with db() as conn:
        rows = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    return jsonify([dict(r) for r in rows]), 200


@app.route("/products/<int:pid>", methods=["GET"])
def get_product(pid):
    with db() as conn:
        row = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
    if row is None:
        return jsonify(error="not found"), 404
    return jsonify(dict(row)), 200


@app.route("/products", methods=["POST"])
def create_product():
    data = request.get_json(force=True)
    name = data.get("name")
    if not name:
        return jsonify(error="name is required"), 400
    qty = int(data.get("quantity", 0))
    price = float(data.get("price", 0))
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO products (name, quantity, price) VALUES (?,?,?)",
            (name, qty, price),
        )
        pid = cur.lastrowid
    return jsonify(id=pid, name=name, quantity=qty, price=price), 201


@app.route("/products/<int:pid>", methods=["PUT"])
def update_product(pid):
    data = request.get_json(force=True)
    with db() as conn:
        row = conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        if row is None:
            return jsonify(error="not found"), 404
        name = data.get("name", row["name"])
        qty = int(data.get("quantity", row["quantity"]))
        price = float(data.get("price", row["price"]))
        conn.execute(
            "UPDATE products SET name=?, quantity=?, price=? WHERE id=?",
            (name, qty, price, pid),
        )
    return jsonify(id=pid, name=name, quantity=qty, price=price), 200


@app.route("/products/<int:pid>", methods=["DELETE"])
def delete_product(pid):
    with db() as conn:
        cur = conn.execute("DELETE FROM products WHERE id=?", (pid,))
        if cur.rowcount == 0:
            return jsonify(error="not found"), 404
    return jsonify(deleted=pid), 200


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
