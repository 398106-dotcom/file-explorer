Python Flask File Explorer

A web-based file explorer built with Flask.
Browse directories, manage files, and interact with a sandboxed file system directly from your browser.

FEATURES:

- User accounts: register, login, logout
- Per-user folders: each user sees only their own files
- Browse files & directories: navigate subfolders
- File management: upload, rename, delete files and folders (including non-empty folders)
- Edit text files: read and save .txt files directly in the browser
- Download files: download any file from your folder
- Breadcrumb navigation: easily move between directories
- Icons for files/folders: intuitive interface with emoji icons
- Sandboxed root directory: prevents access to files outside the app

INSTALL:

1. Clone the repository:
   git clone https://github.com/398106-dotcom/file-explorer
2. Enter the folder:
   cd file-explorer
3. Install dependencies:
   pip install -r requirements.txt


SECURITY NOTES:

- Uses a strong secret key for session management
- User passwords are hashed with werkzeug.security
- Each user’s files are isolated in their own folder

Enjoy your web-based Python file explorer!
