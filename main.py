from flask import Flask, send_from_directory, render_template_string, abort
import os

app = Flask(__name__)

# Root directory for file explorer
ROOT_DIR = os.path.abspath("shared")

TEMPLATE = """
<!doctype html>
<title>File Explorer</title>
<h2>Index of /{{ path }}</h2>
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
    return render_template_string(TEMPLATE, entries=sorted(entries), path=subpath, parent=parent)

@app.route('/download/<path:subpath>')
def download(subpath):
    abs_path = safe_join(ROOT_DIR, subpath)
    if abs_path is None or not os.path.isfile(abs_path):
        abort(404)
    directory = os.path.dirname(abs_path)
    filename = os.path.basename(abs_path)
    return send_from_directory(directory, filename, as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # Works locally & on hosts
    app.run(host="0.0.0.0", port=port, debug=True)
