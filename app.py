from flask import Flask, render_template, request, send_file, redirect, url_for, flash, session, abort
from io import BytesIO
import qrcode
from qrcode.image.pil import PilImage
from PIL import Image
from datetime import datetime
import os, sqlite3, uuid
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), "data.sqlite")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS qrs(
        id TEXT PRIMARY KEY,
        url TEXT NOT NULL,
        name TEXT,
        folder TEXT,
        password_hash TEXT,
        created_at TEXT
    )""")
    conn.commit()
    conn.close()

def generate_qr_png(data: str, box_size: int = 10, border: int = 4, fill_color="black", back_color="white"):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fill_color, back_color=back_color, image_factory=PilImage)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret")
init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    qr_png_b64 = None
    form = {"url":"", "name":"", "folder":"", "password":""}
    slug = None
    if request.method == "POST":
        form["url"] = (request.form.get("url") or "").strip()
        form["name"] = (request.form.get("name") or "").strip()
        form["folder"] = (request.form.get("folder") or "").strip()
        form["password"] = (request.form.get("password") or "").strip()
        action = request.form.get("action")
        if not form["url"]:
            flash("URLを入力してください。", "error")
        else:
            if action == "preview":
                target = form["url"]
                buf = generate_qr_png(target, box_size=8, border=3)
                import base64
                qr_png_b64 = base64.b64encode(buf.read()).decode("ascii")
            else:
                slug = uuid.uuid4().hex[:10]
                pwd_hash = generate_password_hash(form["password"]) if form["password"] else None
                conn = get_db()
                conn.execute("INSERT INTO qrs(id,url,name,folder,password_hash,created_at) VALUES(?,?,?,?,?,?)",
                             (slug, form["url"], form["name"], form["folder"], pwd_hash, datetime.utcnow().isoformat()))
                conn.commit()
                conn.close()
                qr_url = url_for("resolve", slug=slug, _external=True)
                buf = generate_qr_png(qr_url, box_size=8, border=3)
                import base64
                qr_png_b64 = base64.b64encode(buf.read()).decode("ascii")
                flash("QRを作成しました。ダウンロードできます。", "ok")
    return render_template("index.html", qr_png_b64=qr_png_b64, form=form, slug=slug)

@app.post("/download")
def download():
    slug = request.form.get("slug")
    url = request.form.get("url")
    name = (request.form.get("name") or "my-qr").strip()
    action = request.form.get("action")
    if slug:
        qr_target = url_for("resolve", slug=slug, _external=True)
    else:
        if not url:
            flash("URLを入力してください。", "error")
            return redirect(url_for("index"))
        qr_target = url
    buf = generate_qr_png(qr_target, box_size=10, border=3)
    filename = f"{name or 'my-qr'}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.png"
    return send_file(buf, mimetype="image/png", as_attachment=True, download_name=filename)

@app.route("/r/<slug>", methods=["GET", "POST"])
def resolve(slug):
    conn = get_db()
    row = conn.execute("SELECT * FROM qrs WHERE id=?", (slug,)).fetchone()
    conn.close()
    if not row:
        abort(404)
    unlocked = session.get(f"unlocked:{slug}") is True
    if row["password_hash"] and not unlocked:
        if request.method == "POST":
            pw = (request.form.get("password") or "").strip()
            if pw and check_password_hash(row["password_hash"], pw):
                session[f"unlocked:{slug}"] = True
                return redirect(row["url"])
            else:
                flash("パスワードが違います。", "error")
        return render_template("unlock.html", name=row["name"], slug=slug)
    return redirect(row["url"])

@app.route("/list")
def list_qrs():
    conn = get_db()
    rows = conn.execute("SELECT id, name, folder, url, created_at FROM qrs ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("list.html", rows=rows)

@app.route("/pricing")
def pricing():
    plans = [
        {"id": "monthly", "title": "毎月請求", "price": "¥ 3,000 JPY / 月",  "popular": False},
        {"id": "yearly", "title": "毎年請求", "price": "¥ 1,000 JPY / 月", "popular": True},
    ]
    return render_template("pricing.html", plans=plans)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2000, debug=True)
