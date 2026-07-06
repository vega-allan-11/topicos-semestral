import os
import sqlite3
from flask import Flask, request, jsonify, Response

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


INDEX_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Gestor de Inventario</title>
<style>
  :root {
    --bg: #0f172a; --card: #1e293b; --border: #334155;
    --text: #e2e8f0; --muted: #94a3b8; --accent: #38bdf8; --danger: #f87171;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
    background: var(--bg); color: var(--text); padding: 2rem 1rem;
  }
  .wrap { max-width: 820px; margin: 0 auto; }
  h1 { font-size: 1.5rem; margin: 0 0 0.25rem; }
  p.sub { color: var(--muted); margin: 0 0 1.5rem; font-size: 0.9rem; }
  .card { background: var(--card); border: 1px solid var(--border);
          border-radius: 10px; padding: 1.25rem; margin-bottom: 1.5rem; }
  form { display: grid; grid-template-columns: 2fr 1fr 1fr auto; gap: 0.75rem; }
  input {
    background: var(--bg); border: 1px solid var(--border); color: var(--text);
    padding: 0.6rem 0.75rem; border-radius: 6px; font-size: 0.9rem; width: 100%;
  }
  input:focus { outline: none; border-color: var(--accent); }
  button {
    background: var(--accent); color: #082f49; border: none; font-weight: 600;
    padding: 0.6rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.9rem;
  }
  button:hover { opacity: 0.9; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 0.7rem 0.5rem; border-bottom: 1px solid var(--border); }
  th { color: var(--muted); font-weight: 600; font-size: 0.8rem; text-transform: uppercase; }
  td.actions { text-align: right; }
  .del { background: none; color: var(--danger); border: 1px solid var(--border);
         padding: 0.35rem 0.7rem; font-weight: 500; }
  .del:hover { border-color: var(--danger); }
  .empty { color: var(--muted); text-align: center; padding: 2rem; }
  @media (max-width: 640px) { form { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="wrap">
  <h1>Gestor de Inventario</h1>
  <p class="sub">Azure Container Instances &middot; API Flask + SQLite</p>

  <div class="card">
    <form id="form">
      <input id="name" placeholder="Nombre del producto" required>
      <input id="quantity" type="number" placeholder="Cantidad" min="0" value="0">
      <input id="price" type="number" step="0.01" placeholder="Precio" min="0" value="0">
      <button type="submit">Agregar</button>
    </form>
  </div>

  <div class="card">
    <table>
      <thead>
        <tr><th>ID</th><th>Nombre</th><th>Cantidad</th><th>Precio</th><th></th></tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
    <div id="empty" class="empty" style="display:none">Sin productos registrados.</div>
  </div>
</div>

<script>
const API = "/products";

async function load() {
  const res = await fetch(API);
  const items = await res.json();
  const tbody = document.getElementById("tbody");
  const empty = document.getElementById("empty");
  tbody.innerHTML = "";
  empty.style.display = items.length ? "none" : "block";
  for (const p of items) {
    const tr = document.createElement("tr");
    tr.innerHTML =
      `<td>${p.id}</td><td>${p.name}</td><td>${p.quantity}</td>` +
      `<td>$${Number(p.price).toFixed(2)}</td>` +
      `<td class="actions"><button class="del" data-id="${p.id}">Eliminar</button></td>`;
    tbody.appendChild(tr);
  }
  document.querySelectorAll(".del").forEach(b =>
    b.onclick = () => remove(b.dataset.id));
}

async function remove(id) {
  await fetch(`${API}/${id}`, { method: "DELETE" });
  load();
}

document.getElementById("form").onsubmit = async (e) => {
  e.preventDefault();
  const body = {
    name: document.getElementById("name").value,
    quantity: parseInt(document.getElementById("quantity").value || "0"),
    price: parseFloat(document.getElementById("price").value || "0"),
  };
  await fetch(API, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  e.target.reset();
  load();
};

load();
</script>
</body>
</html>"""


@app.route("/")
def index():
    return Response(INDEX_HTML, mimetype="text/html")


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
