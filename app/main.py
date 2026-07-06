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
  * { box-sizing: border-box; }
  body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
         margin: 0; background: #f4f6f8; color: #1f2937; }
  header { background: #0b5394; color: #fff; padding: 20px 24px; }
  header h1 { margin: 0; font-size: 20px; font-weight: 600; }
  main { max-width: 900px; margin: 24px auto; padding: 0 16px; }
  .card { background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,.1);
          padding: 20px; margin-bottom: 20px; }
  h2 { font-size: 15px; margin: 0 0 14px; color: #374151; }
  form { display: flex; gap: 10px; flex-wrap: wrap; }
  input { padding: 9px 11px; border: 1px solid #d1d5db; border-radius: 6px; font-size: 14px; width: 100%; }
  #f input[name="name"] { flex: 2; min-width: 160px; }
  #f input[name="quantity"], #f input[name="price"] { flex: 1; min-width: 90px; }
  button { padding: 9px 16px; border: 0; border-radius: 6px; background: #0b5394;
           color: #fff; font-size: 14px; cursor: pointer; }
  button:hover { background: #094074; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid #eef0f2; font-size: 14px; vertical-align: middle; }
  th { color: #6b7280; font-weight: 600; font-size: 12px; text-transform: uppercase; }
  .actions { display: flex; gap: 6px; }
  .btn-sm { padding: 5px 10px; font-size: 12px; }
  .edit { background: #0b5394; }
  .del { background: #dc2626; }
  .del:hover { background: #b91c1c; }
  .save { background: #16a34a; }
  .save:hover { background: #15803d; }
  .cancel { background: #6b7280; }
  .cancel:hover { background: #4b5563; }
  .cell-input { width: 100%; padding: 6px 8px; font-size: 13px; }
  .empty { color: #9ca3af; padding: 16px 12px; font-size: 14px; }
</style>
</head>
<body>
<header><h1>Gestor de Inventario</h1></header>
<main>
  <div class="card">
    <h2>Agregar producto</h2>
    <form id="f">
      <input name="name" placeholder="Nombre" required>
      <input name="quantity" type="number" placeholder="Cantidad" value="0" min="0">
      <input name="price" type="number" step="0.01" placeholder="Precio" value="0" min="0">
      <button type="submit">Agregar</button>
    </form>
  </div>
  <div class="card">
    <h2>Productos</h2>
    <table>
      <thead><tr><th>ID</th><th>Nombre</th><th>Cantidad</th><th>Precio</th><th>Acciones</th></tr></thead>
      <tbody id="rows"></tbody>
    </table>
    <div id="empty" class="empty" style="display:none">Sin productos registrados.</div>
  </div>
</main>
<script>
const rows = document.getElementById('rows');
const empty = document.getElementById('empty');
let editingId = null;

async function load() {
  const r = await fetch('/products');
  const data = await r.json();
  rows.innerHTML = '';
  empty.style.display = data.length ? 'none' : 'block';
  for (const p of data) {
    rows.appendChild(p.id === editingId ? editRow(p) : viewRow(p));
  }
}

function viewRow(p) {
  const tr = document.createElement('tr');
  tr.innerHTML = `<td>${p.id}</td><td>${p.name}</td><td>${p.quantity}</td>
    <td>$${Number(p.price).toFixed(2)}</td>
    <td><div class="actions">
      <button class="btn-sm edit" data-act="edit" data-id="${p.id}">Editar</button>
      <button class="btn-sm del" data-act="del" data-id="${p.id}">Eliminar</button>
    </div></td>`;
  return tr;
}

function editRow(p) {
  const tr = document.createElement('tr');
  tr.innerHTML = `<td>${p.id}</td>
    <td><input class="cell-input" id="e-name" value="${p.name}"></td>
    <td><input class="cell-input" id="e-qty" type="number" min="0" value="${p.quantity}"></td>
    <td><input class="cell-input" id="e-price" type="number" step="0.01" min="0" value="${p.price}"></td>
    <td><div class="actions">
      <button class="btn-sm save" data-act="save" data-id="${p.id}">Guardar</button>
      <button class="btn-sm cancel" data-act="cancel">Cancelar</button>
    </div></td>`;
  return tr;
}

document.getElementById('f').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  await fetch('/products', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: fd.get('name'),
      quantity: Number(fd.get('quantity')),
      price: Number(fd.get('price'))
    })
  });
  e.target.reset();
  load();
});

rows.addEventListener('click', async (e) => {
  const act = e.target.dataset.act;
  const id = e.target.dataset.id;
  if (act === 'del') {
    await fetch('/products/' + id, { method: 'DELETE' });
    load();
  } else if (act === 'edit') {
    editingId = Number(id);
    load();
  } else if (act === 'cancel') {
    editingId = null;
    load();
  } else if (act === 'save') {
    await fetch('/products/' + id, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: document.getElementById('e-name').value,
        quantity: Number(document.getElementById('e-qty').value),
        price: Number(document.getElementById('e-price').value)
      })
    });
    editingId = null;
    load();
  }
});

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
