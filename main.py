import os
import shutil
import json
from functools import wraps
from flask import Flask, send_from_directory, render_template_string, abort, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "YOUR SECRET KEY"
# Limit uploads to 50MB
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

ROOT_DIR = os.path.abspath("shared")
USERS_FILE = "users.json"

# Ensure root folder exists
if not os.path.exists(ROOT_DIR):
    os.makedirs(ROOT_DIR)

# ---------- User helpers ----------
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            flash("Please login first")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ---------- Templates ----------
LOGIN_TEMPLATE = """
<h2>Login</h2>
<form method="POST">
  <input type="text" name="username" placeholder="Username" required>
  <input type="password" name="password" placeholder="Password" required>
  <input type="submit" value="Login">
</form>
<p>Or <a href="{{ url_for('register') }}">Register</a></p>
{% with messages = get_flashed_messages() %}
  {% if messages %}
    <ul style="color:red;">
      {% for msg in messages %}
        <li>{{ msg }}</li>
      {% endfor %}
    </ul>
  {% endif %}
{% endwith %}
"""

REGISTER_TEMPLATE = """
<h2>Register</h2>
<form method="POST">
  <input type="text" name="username" placeholder="Username" required>
  <input type="password" name="password" placeholder="Password" required>
  <input type="submit" value="Register">
</form>
<p>Or <a href="{{ url_for('login') }}">Login</a></p>
{% with messages = get_flashed_messages() %}
  {% if messages %}
    <ul style="color:red;">
      {% for msg in messages %}
        <li>{{ msg }}</li>
      {% endfor %}
    </ul>
  {% endif %}
{% endwith %}
"""

TEMPLATE = """
<!doctype html>
<title>File Explorer</title>
<h2>Index of /{{ path }}</h2>
<p>Logged in as {{ username }} | <a href="{{ url_for('logout') }}">Logout</a></p>

<!-- Breadcrumbs -->
<p>
  {% for crumb, crumb_path in breadcrumbs %}
    <a href="{{ url_for('browse', subpath=crumb_path) }}">{{ crumb }}</a> /
  {% endfor %}
</p>

<form method="POST" action="{{ url_for('upload') }}" enctype="multipart/form-data">
  <input type="file" name="file">
  <input type="hidden" name="current_path" value="{{ path }}">
  <input type="submit" value="Upload File">
</form>

<form method="POST" action="{{ url_for('create_folder') }}">
  <input type="text" name="folder_name" placeholder="New folder name" required>
  <input type="hidden" name="current_path" value="{{ path }}">
  <input type="submit" value="Create Folder">
</form>

<!-- NEW: Create File Form -->
<form method="POST" action="{{ url_for('create_file') }}">
  <input type="text" name="file_name" placeholder="New file name" required>
  <input type="hidden" name="current_path" value="{{ path }}">
  <input type="submit" value="Create File">
</form>

{% with messages = get_flashed_messages() %}
  {% if messages %}
    <ul style="color:red;">
      {% for msg in messages %}
        <li>{{ msg }}</li>
      {% endfor %}
    </ul>
  {% endif %}
{% endwith %}

<ul>
  {% if parent %}
    <li><a href="{{ url_for('browse', subpath=parent) }}">.. (parent)</a></li>
  {% endif %}
  {% for name, is_dir in entries %}
    {% if is_dir %}
      <li>
        📁 <a href="{{ url_for('browse', subpath=(path + '/' + name).lstrip('/')) }}">{{ name }}/</a>
        [<a href="{{ url_for('rename', subpath=(path + '/' + name).lstrip('/')) }}">Rename</a>]
        [<a href="{{ url_for('delete', subpath=(path + '/' + name).lstrip('/')) }}">Delete</a>]
      </li>
    {% else %}
      <li>
        📄 <a href="{{ url_for('download', subpath=(path + '/' + name).lstrip('/')) }}">{{ name }}</a>
        [<a href="{{ url_for('read_file', subpath=(path + '/' + name).lstrip('/')) }}">Read/Edit</a>]
        [<a href="{{ url_for('rename', subpath=(path + '/' + name).lstrip('/')) }}">Rename</a>]
        [<a href="{{ url_for('delete', subpath=(path + '/' + name).lstrip('/')) }}">Delete</a>]
      </li>
    {% endif %}
  {% endfor %}
</ul>
"""

READ_EDIT_TEMPLATE = """
<h2>Edit: {{ filename }}</h2>
<form method="POST">
  <textarea name="content" rows="20" cols="80">{{ content }}</textarea><br>
  <input type="submit" value="Save">
</form>
<p><a href="{{ url_for('browse', subpath=parent) }}">Back</a></p>
"""

RENAME_TEMPLATE = """
<h2>Rename: {{ old_name }}</h2>
<form method="POST">
  <input type="text" name="new_name" value="{{ old_name }}" required>
  <input type="submit" value="Rename">
</form>
<a href="{{ url_for('browse', subpath=parent) }}">Cancel</a>
"""

# ---------- Helper Functions ----------
def safe_join(root, subpath):
    newpath = os.path.normpath(os.path.join(root, subpath))
    if os.path.commonpath([newpath, root]) != root:
        return None
    return newpath

def make_breadcrumbs(path):
    crumbs = [("", "")]
    if path:
        parts = path.split("/")
        for i in range(len(parts)):
            crumb_path = "/".join(parts[:i+1])
            crumbs.append((parts[i], crumb_path))
    return crumbs

def get_user_folder():
    username = session["username"]
    user_folder = os.path.join(ROOT_DIR, username)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
        if not os.listdir(user_folder):
            sample_file = os.path.join(user_folder, "test.txt")
            with open(sample_file, "w") as f:
                f.write("Hello! (test!).\n")
    return user_folder

# ---------- User Routes ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        users = load_users()
        if username in users:
            flash("Username already exists!")
            return redirect(url_for("register"))
        users[username] = generate_password_hash(password)
        save_users(users)
        flash("Registered successfully! Login now.")
        return redirect(url_for("login"))
    return render_template_string(REGISTER_TEMPLATE)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        users = load_users()
        if username in users and check_password_hash(users[username], password):
            session["username"] = username
            flash("Logged in successfully!")
            return redirect(url_for("browse"))
        flash("Invalid credentials")
        return redirect(url_for("login"))
    return render_template_string(LOGIN_TEMPLATE)

@app.route("/logout")
@login_required
def logout():
    session.pop("username", None)
    flash("Logged out")
    return redirect(url_for("login"))

# ---------- File Explorer Routes ----------
@app.route("/", defaults={"subpath": ""})
@app.route("/browse/<path:subpath>")
@login_required
def browse(subpath):
    user_folder = get_user_folder()
    abs_path = safe_join(user_folder, subpath)
    if abs_path is None or not os.path.isdir(abs_path):
        abort(404)

    entries = [(name, os.path.isdir(os.path.join(abs_path, name))) 
               for name in os.listdir(abs_path) if not name.startswith('.')]

    parent = os.path.dirname(subpath) if subpath else None
    breadcrumbs = make_breadcrumbs(subpath)
    return render_template_string(TEMPLATE, entries=sorted(entries), path=subpath, parent=parent, breadcrumbs=breadcrumbs, username=session["username"])

@app.route('/download/<path:subpath>')
@login_required
def download(subpath):
    user_folder = get_user_folder()
    abs_path = safe_join(user_folder, subpath)
    if abs_path is None or not os.path.isfile(abs_path):
        abort(404)
    return send_from_directory(os.path.dirname(abs_path), os.path.basename(abs_path), as_attachment=True)

@app.route('/read/<path:subpath>', methods=['GET', 'POST'])
@login_required
def read_file(subpath):
    user_folder = get_user_folder()
    abs_path = safe_join(user_folder, subpath)
    if abs_path is None or not os.path.isfile(abs_path):
        abort(404)
    parent = os.path.dirname(subpath)
    if request.method == "POST":
        content = request.form.get("content", "")
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        flash(f"Saved {os.path.basename(subpath)}")
        return redirect(url_for('browse', subpath=parent))
    with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    return render_template_string(READ_EDIT_TEMPLATE, filename=os.path.basename(subpath), content=content, parent=parent)

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    if 'file' not in request.files:
        flash("No file part")
        return redirect(request.referrer)
    file = request.files['file']
    if file.filename == '':
        flash("No selected file")
        return redirect(request.referrer)
    current_path = request.form.get('current_path', '')
    user_folder = get_user_folder()
    target_dir = safe_join(user_folder, current_path)
    if target_dir is None or not os.path.isdir(target_dir):
        flash("Invalid target folder")
        return redirect(request.referrer)
    save_path = os.path.join(target_dir, file.filename)
    file.save(save_path)
    return redirect(url_for('browse', subpath=current_path))

@app.route('/create_folder', methods=['POST'])
@login_required
def create_folder():
    folder_name = request.form.get('folder_name')
    current_path = request.form.get('current_path', '')
    user_folder = get_user_folder()
    target_dir = safe_join(user_folder, current_path)
    if folder_name and target_dir:
        new_folder_path = os.path.join(target_dir, folder_name)
        if not os.path.exists(new_folder_path):
            os.makedirs(new_folder_path)
    return redirect(url_for('browse', subpath=current_path))

# ---------- NEW: Create File ----------
@app.route('/create_file', methods=['POST'])
@login_required
def create_file():
    file_name = request.form.get('file_name')
    current_path = request.form.get('current_path', '')
    user_folder = get_user_folder()
    target_dir = safe_join(user_folder, current_path)

    if not file_name or not target_dir:
        flash("Invalid file name or path")
        return redirect(request.referrer)

    new_file_path = os.path.join(target_dir, file_name)
    if os.path.exists(new_file_path):
        flash("File already exists!")
    else:
        with open(new_file_path, 'w', encoding='utf-8') as f:
            f.write("")  # empty content
        flash(f"Created new file: {file_name}")

    return redirect(url_for('browse', subpath=current_path))

@app.route('/delete/<path:subpath>')
@login_required
def delete(subpath):
    user_folder = get_user_folder()
    abs_path = safe_join(user_folder, subpath)
    if abs_path is None or not os.path.exists(abs_path):
        flash("File or folder does not exist")
        return redirect(request.referrer)
    try:
        if os.path.isfile(abs_path):
            os.remove(abs_path)
        elif os.path.isdir(abs_path):
            shutil.rmtree(abs_path)
        flash(f"Deleted: {subpath}")
    except Exception as e:
        flash(f"Error deleting {subpath}: {e}")
    return redirect(request.referrer)

@app.route('/rename/<path:subpath>', methods=['GET', 'POST'])
@login_required
def rename(subpath):
    user_folder = get_user_folder()
    abs_path = safe_join(user_folder, subpath)
    if abs_path is None or not os.path.exists(abs_path):
        flash("File or folder does not exist")
        return redirect(request.referrer)
    parent = os.path.dirname(subpath)
    if request.method == 'POST':
        new_name = request.form.get('new_name')
        if new_name:
            new_path = os.path.join(user_folder, parent, new_name) if parent else os.path.join(user_folder, new_name)
            os.rename(abs_path, new_path)
            flash(f"Renamed to {new_name}")
            return redirect(url_for('browse', subpath=parent))
    return render_template_string(RENAME_TEMPLATE, old_name=os.path.basename(subpath), parent=parent)

# ---------- Run App ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
