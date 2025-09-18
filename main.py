import os
from flask import Flask, send_from_directory, render_template_string, abort, request, redirect, url_for

app = Flask(__name__)

# Root folder
ROOT_DIR = os.path.abspath("shared")

# Ensure folder exists
if not os.path.exists(ROOT_DIR):
    os.makedirs(ROOT_DIR)

# Add sample file if folder is empty
if not os.listdir(ROOT_DIR):
    sample_file = os.path.join(ROOT_DIR, "hello.txt")
    with open(sample_file, "w") as f:
        f.write("Hello! This is a sample file for your Python file explorer.\n")

# HTML template with upload form
TEMPLATE = """
<!doctype html>
<title>File Explorer</title>
<h2>Index of /{{ path }}</h2>
<form method="POST" action="{{ url_for('upload') }}" enctype="multipart/form-data">
  <input type="file" name="file">
  <input type="submit" value="Upload">
</form>
<ul>
  {% if parent %}
    <li><a href="{{ url_for('browse', subpath=parent) }}">.. (parent)</a></li>
  {% endif %}
  {% for name, is_dir in entries %}
    {% if is_dir %}
      <li><a href="{{ url_for('browse', subpath=(path + '/' + name).lstrip('/')) }}">{{ name }}/</a></li>
    {% else %}
      <li><a href="{{ url_for('download', subpath=(path + '/' + name).lstrip('/')) }}">{{ name }}</a></li>
    {% endif %}
  {% endfor %}
</ul>
"""

def safe_join(root, subpath):
    """Prevent directory traversal outside ROOT_DIR."""
    newpath = os.path.normpath(os.path.join(root, subpath))
    if os.path.commonpath([newpath, root]) != root:
        return None
    return newpath

@app.route('/', defaults={'subpath': ''})
@app.route('/browse/<path:subpath>')
def browse(subpath):
    abs_path = safe_join(ROOT_DIR, subpath)
    if abs_path is None or not os.path.isdir(abs_path):
        abort(404)

    entries = []
    for name in os.listdir(abs_path):
        if name.startswith('.'):
            continue
        full = os.path.join(abs_path, name)
        entries.append((name, os.path.isdir(full)))

    parent = None
    if subpath:
        parent = os.path.dirname(subpath)

    return render_template_string(
        TEMPLATE,
        entries=sorted(entries),
        path=subpath,
        parent=parent
    )

@app.route('/download/<path:subpath>')
def download(subpath):
    abs_path = safe_join(ROOT_DIR, subpath)
    if abs_path is None or not os.path.isfile(abs_path):
        abort(404)
    directory = os.path.dirname(abs_path)
    filename = os.path.basename(abs_path)
    return send_from_directory(directory, filename, as_attachment=True)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(request.referrer)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.referrer)
    save_path = os.path.join(ROOT_DIR, file.filename)
    file.save(save_path)
    return redirect(url_for('browse', subpath=''))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
