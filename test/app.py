from flask import Flask, request, render_template_string, redirect, url_for, session, send_from_directory, flash
import os
from pathlib import Path
from werkzeug.utils import secure_filename
import base64
import html

# -------------------------------------------------------------
# ⚠️ DEMO MỤC ĐÍCH HỌC TẬP — KHÔNG AN TOÀN, ĐỪNG ĐƯA LÊN INTERNET
# Ứng dụng này cố ý có "cửa hậu" (backdoor):
# - Nếu upload bất kỳ file nào mà NỘI DUNG chứa chuỗi b"admin:admin123"
#   thì bạn được nâng quyền admin trong phiên làm việc hiện tại.
# - Admin có thể xem flag.txt và ảnh "ẩn".
# - Chỉ dùng cục bộ để học/thử nghiệm CTF.
# -------------------------------------------------------------

app = Flask(__name__)
app.secret_key = "dev-secret-please-change"  # đổi giá trị nếu muốn

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
HIDDEN_DIR = DATA_DIR / "hidden_images"
FLAG_FILE = DATA_DIR / "flag.txt"

MAGIC_BYTES = b"admin:admin123"

# Helper: b64 decode an toàn kể cả khi thiếu padding
def b64decode_padded(s):
    if isinstance(s, bytes):
        try:
            s = s.decode("ascii", "ignore")
        except Exception:
            s = str(s)
    s = (s or "").strip()
    missing = (-len(s)) % 4
    if missing:
        s += "=" * missing
    try:
        return base64.b64decode(s)
    except Exception:
        return base64.b64decode(s + "==")

# ---------- Khởi tạo thư mục & dữ liệu mẫu ----------
def ensure_dirs_and_seed():
    DATA_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    HIDDEN_DIR.mkdir(parents=True, exist_ok=True)

    if not FLAG_FILE.exists():
        FLAG_FILE.write_text("FLAG{demo_flask_backdoor}", encoding="utf-8")

    # Gieo 3 ảnh PNG 1x1 siêu nhỏ (base64), coi như ảnh "ẩn"
    png_black = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
    )
    png_white = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGP4zwAAAgUBtQEf6yQAAAAASUVORK5CYII="
    )
    png_gray = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGP4zwAAAgUBd5v4tQAAAAASUVORK5CYII="
    )

    samples = [
        ("secret1.png", png_black),
        ("secret2.png", png_white),
        ("secret3.png", png_gray),
    ]
    for name, b64 in samples:
        fpath = HIDDEN_DIR / name
        if not fpath.exists():
            fpath.write_bytes(b64decode_padded(b64))

ensure_dirs_and_seed()

# ---------- Helpers ----------
def is_admin():
    return bool(session.get("is_admin"))

def require_admin():
    if not is_admin():
        return ("Bạn không có quyền. Hãy upload một file chứa chuỗi 'admin:admin123' để vào admin.", 403)
    return None

def render_page(title, body_html):
    return render_template_string(
        BASE_HTML,
        title=title,
        is_admin=is_admin(),
        content=body_html,
    )

# ---------- Giao diện phong cách web bán sách ----------
BASE_HTML = """
<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{{ title or 'BookTown — Cửa hàng sách' }}</title>
  <style>
    :root{
      --bg:#f7f8fc;
      --card:#ffffff;
      --text:#0f172a;
      --muted:#64748b;
      --brand:#6d28d9;
      --brand2:#9333ea;
      --line:#e5e7eb;
      --success:#16a34a;
      --warning:#a16207;
    }
    *{box-sizing:border-box}
    body{
      margin:0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, "Noto Sans", "Helvetica Neue", sans-serif;
      background: linear-gradient(180deg, #f5f3ff 0%, var(--bg) 60%);
      color: var(--text);
    }
    a{color:var(--brand); text-decoration:none}
    a:hover{text-decoration:underline}
    .container{max-width:1080px; margin:0 auto; padding:24px}
    /* NAVBAR */
    .nav{
      position:sticky; top:0; z-index:10;
      background:rgba(255,255,255,0.8); backdrop-filter: blur(8px);
      border-bottom:1px solid var(--line);
    }
    .nav-inner{display:flex; align-items:center; justify-content:space-between; gap:16px; padding:14px 24px; max-width:1080px; margin:0 auto;}
    .logo{
      display:flex; align-items:center; gap:10px; font-weight:800; font-size:20px; letter-spacing:.2px;
      color: var(--brand2);
    }
    .logo .mark{
      width:32px; height:32px; display:grid; place-items:center; border-radius:8px;
      background: radial-gradient(100% 100% at 0% 0%, var(--brand) 0%, var(--brand2) 100%);
      color:white; font-size:18px;
      box-shadow: 0 6px 20px rgba(109,40,217,.25);
    }
    .nav-links{display:flex; align-items:center; gap:18px; flex-wrap:wrap}
    .nav-links a{color:#334155; font-weight:600}
    .nav-cta{display:flex; align-items:center; gap:10px}
    .btn{
      display:inline-flex; align-items:center; justify-content:center; gap:8px;
      padding:10px 14px; border-radius:12px; border:1px solid var(--line);
      background: var(--card); color:#1f2937; font-weight:700; cursor:pointer;
      transition: transform .04s ease, box-shadow .2s ease, background .2s ease;
    }
    .btn:hover{transform:translateY(-1px); box-shadow:0 8px 20px rgba(17,24,39,.06)}
    .btn.brand{
      background: linear-gradient(135deg, var(--brand) 0%, var(--brand2) 100%);
      color:white; border:none;
      box-shadow: 0 10px 20px rgba(147,51,234,.22);
    }
    .pill{
      display:inline-flex; align-items:center; gap:8px; padding:6px 10px; border-radius:999px;
      background:#ede9fe; color:#5b21b6; font-size:12px; font-weight:700;
    }
    /* HERO */
    .hero{
      display:grid; gap:18px; padding:40px 24px;
      background: radial-gradient(120% 120% at 10% 0%, rgba(147,51,234,.08) 0%, rgba(255,255,255,0) 60%);
      border-bottom:1px solid var(--line);
    }
    .hero h1{font-size:36px; line-height:1.2; margin:0; letter-spacing:.2px}
    .hero p{color:var(--muted); margin:6px 0 0 0; max-width:700px}
    .actions{display:flex; gap:10px; flex-wrap:wrap; margin-top:8px}
    /* LAYOUT */
    .grid{display:grid; grid-template-columns:repeat(12,1fr); gap:18px}
    .card{grid-column: span 12; background:var(--card); border:1px solid var(--line); border-radius:16px; padding:16px}
    @media(min-width:720px){
      .card.half{grid-column: span 6}
    }
    .flash{background:#fffae5; border:1px solid #f0e1a0; padding:10px 12px; border-radius:10px; margin:12px 0}
    /* BOOK CARD */
    .book-grid{display:grid; grid-template-columns:repeat(auto-fill, minmax(160px, 1fr)); gap:16px}
    .book{
      background: white; border:1px solid var(--line); border-radius:14px; overflow:hidden;
      transition: transform .08s ease, box-shadow .2s ease;
    }
    .book:hover{transform:translateY(-2px); box-shadow:0 14px 28px rgba(17,24,39,.08)}
    .book .cover{aspect-ratio: 3/4; width:100%; display:block; object-fit:cover; background:#f4f4f8}
    .book .meta{padding:12px}
    .book .title{font-weight:800; font-size:14px; line-height:1.3}
    .book .price{font-weight:900; margin-top:6px}
    .muted{color:var(--muted)}
    /* FORMS */
    .form{display:grid; gap:10px}
    .input{
      background:white; border:1px solid var(--line); border-radius:12px; padding:10px 12px; font-size:14px;
      outline:none;
    }
    .hint{font-size:12px; color:var(--muted)}
    /* FOOTER */
    .foot{padding:24px; text-align:center; color:var(--muted); font-size:13px}
    /* CONTENT SLOT */
    .content{margin-top:18px}
  </style>
</head>
<body>
  <!-- NAVBAR -->
  <div class="nav">
    <div class="nav-inner">
      <a class="logo" href="{{ url_for('home') }}">
        <span class="mark">📚</span> <span>BookTown</span>
      </a>
      <div class="nav-links">
        <a href="{{ url_for('home') }}">Trang chủ</a>
        <a href="{{ url_for('upload') }}">Thêm sách</a>
        {% if is_admin %}
          <a href="{{ url_for('admin_panel') }}">Quản trị</a>
          <a href="{{ url_for('logout') }}">Đăng xuất</a>
        {% endif %}
      </div>
      <div class="nav-cta">
        <a class="btn" href="{{ url_for('upload') }}">📤 Tải lên</a>
        {% if not is_admin %}
          <span class="pill">Khách</span>
        {% else %}
          <span class="pill">Admin</span>
        {% endif %}
      </div>
    </div>
  </div>

  <!-- HERO -->
  <div class="hero container">
    <span class="pill">Cửa hàng sách</span>
    <h1>{{ title or 'BookTown — Khám phá kho sách của bạn' }}</h1>
    <p>Giao diện đã được tùy biến theo phong cách web bán sách: thẻ sách, lưới sản phẩm, và các nút hành động rõ ràng. Bạn có thể dùng trang "Thêm sách" để tải file (demo), hoặc mở trang Quản trị nếu là admin.</p>
    <div class="actions">
      <a class="btn brand" href="{{ url_for('upload') }}">+ Thêm sách mới</a>
      {% if is_admin %}
        <a class="btn" href="{{ url_for('admin_panel') }}">Bảng điều khiển</a>
      {% endif %}
    </div>
  </div>

  <!-- MAIN -->
  <div class="container">
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        {% for m in messages %}<div class="flash">{{ m }}</div>{% endfor %}
      {% endif %}
    {% endwith %}

    <div class="content">
      {{ content|safe }}
    </div>
  </div>

  <div class="foot">© {{ 2025 }} BookTown — Giao diện demo bán sách</div>
</body>
</html>
"""

@app.route("/")
def home():
    extra = ""
    if is_admin():
        extra = (
            f"<p class='muted'><strong>Bạn đang là admin.</strong> "
            f"Vào <a href='{url_for('admin_panel')}'>Quản trị</a> để xem flag và bìa sách ẩn.</p>"
        )

    # Khối giới thiệu + CTA
    intro = f"""
    <div class="grid">
      <div class="card half">
        <h3 style="margin:0 0 8px 0">Sách mới cập nhật</h3>
        <p class="muted" style="margin-top:0">Mỗi file bạn tải lên (demo) được coi như một "đầu sách" trong kho.</p>
        <div><a class="btn brand" href="{url_for('upload')}">📚 Nhập sách (upload)</a></div>
        {extra}
      </div>
      <div class="card half">
        <h3 style="margin:0 0 8px 0">Mẹo nhanh</h3>
        <ul style="margin:6px 0 0 18px; color:#334155;">
          <li>Tải lên file có chứa chuỗi <code>admin:admin123</code> để truy cập trang Quản trị (demo backdoor).</li>
          <li>Trong trang Quản trị, bạn có thể xem “bìa sách ẩn”.</li>
          <li>Đây chỉ là bản demo phục vụ học CTF — không dùng trên Internet.</li>
        </ul>
      </div>
    </div>
    """
    return render_page("Trang chủ", intro)

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("Chưa chọn file.")
            return redirect(url_for("upload"))

        filename = secure_filename(file.filename)
        data = file.read()

        # Kiểm tra backdoor
        if MAGIC_BYTES in data:
            session["is_admin"] = True
            flash("Xin chào, admin! Bạn đã được nâng quyền.")
        else:
            flash("Tải lên thành công.")

        # Lưu file vào uploads để tham khảo
        save_path = UPLOAD_DIR / filename
        try:
            save_path.write_bytes(data)
        except Exception as e:
            flash(f"Không thể lưu file: {e}")

        if is_admin():
            return redirect(url_for("admin_panel"))
        return redirect(url_for("upload"))

    # GET
    admin_hint = ""
    if is_admin():
        admin_hint = f"<p class='muted'><strong>Bạn đã là admin.</strong> Vào <a href='{url_for('admin_panel')}'>Quản trị</a>.</p>"

    body = f"""
    <div class="grid">
      <div class="card">
        <h3 style="margin:0 0 8px 0">+ Thêm sách vào kho</h3>
        <p class="muted" style="margin-top:0">Chọn một file để upload. Trong demo này, file được xem như metadata sách.</p>
        <form class="form" action="" method="post" enctype="multipart/form-data">
          <input class="input" type="file" name="file" required />
          <button class="btn brand" type="submit">📤 Tải lên</button>
          <p class="hint">Gợi ý CTF: nội dung chứa <code>admin:admin123</code> sẽ kích hoạt quyền admin.</p>
        </form>
        {admin_hint}
      </div>
    </div>
    """
    return render_page("Thêm sách", body)

@app.route("/admin")
def admin_panel():
    guard = require_admin()
    if guard:
        return guard

    try:
        flag_text = FLAG_FILE.read_text(encoding="utf-8")
    except Exception as e:
        flag_text = f"Không đọc được flag.txt: {e}"

    hidden_files = sorted([p.name for p in HIDDEN_DIR.iterdir() if p.is_file()])

    # Tạo “thẻ sách” cho mỗi ảnh ẩn
    cards = []
    for f in hidden_files:
        src = url_for('admin_image', filename=f)
        title = os.path.splitext(f)[0].replace("_", " ").title()
        card = f"""
        <div class="book">
          <img class="cover" src="{src}" alt="{html.escape(f)}" />
          <div class="meta">
            <div class="title">{html.escape(title)}</div>
            <div class="muted" style="font-size:12px">{html.escape(f)}</div>
            <div class="price">₫ 0</div>
          </div>
        </div>
        """
        cards.append(card)

    gallery = "<div class='book-grid'>" + "".join(cards) + "</div>" if cards else "<p class='muted'>Chưa có bìa sách ẩn.</p>"

    body = f"""
    <div class="grid">
      <div class="card">
        <h3 style="margin:0 0 8px 0">Mã bí mật (flag)</h3>
        <pre style="margin:0; white-space:pre-wrap">{html.escape(flag_text)}</pre>
      </div>
      <div class="card">
        <h3 style="margin:0 0 8px 0">Kho bìa sách ẩn</h3>
        {gallery}
      </div>
    </div>
    """
    return render_page("Quản trị", body)

@app.route("/admin/image/<path:filename>")
def admin_image(filename):
    guard = require_admin()
    if guard:
        return guard
    # Chỉ cho phép serve file nằm trong HIDDEN_DIR
    safe_name = os.path.normpath(filename)
    if safe_name.startswith(".."):
        return ("Tên file không hợp lệ", 400)
    return send_from_directory(HIDDEN_DIR, safe_name)

@app.route("/logout")
def logout():
    session.clear()
    flash("Đã thoát admin.")
    return redirect(url_for("home"))

if __name__ == "__main__":
    # Chạy dev server
    app.run(host="127.0.0.1", port=5000, debug=True)
