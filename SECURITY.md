=============================
FILE EXPLORER SECURITY POLICY
=============================

1. Authentication & Authorization
---------------------------------
- All routes (except /login and /register) require authentication.
- Users must log in to access their files.
- Sessions expire after 30 minutes of inactivity.
- Passwords are securely hashed using industry-standard algorithms.

2. File Path Security
--------------------
- Users can only access their own directories.
- Directory traversal (e.g., ../) is strictly blocked.
- File and folder names are validated to prevent malicious characters.

3. File Upload Security
----------------------
- Only allowed file types can be uploaded.
- Maximum upload size is enforced (e.g., 5MB).
- Filenames are sanitized to remove unsafe characters.
- Uploaded files are stored in user-specific directories, isolated from the system.

4. File Operations
-----------------
- Users can create, read, edit, rename, and delete files/folders only in their own directories.
- All file operations are logged for auditing.
- Backups are maintained to prevent accidental data loss.

5. Input Validation & XSS Protection
-----------------------------------
- All user inputs are validated and sanitized.
- User-provided content is escaped in templates to prevent XSS attacks.
- File/folder names must follow safe naming conventions.

6. Network & HTTPS
-----------------
- The app should be deployed over HTTPS in production.
- Strong TLS configurations are enforced.
- Directory listings are disabled outside the app.

7. Logging & Monitoring
----------------------
- Authentication events (login, logout, failed attempts) are logged.
- File operations are logged.
- Logs are monitored for suspicious activity.

8. Session & Cookie Security
----------------------------
- Cookies are set as HttpOnly and Secure.
- Session IDs are regenerated on login to prevent fixation attacks.
- Session timeout is enforced for idle users.

9. Backup & Recovery
-------------------
- Regular backups of user files and authentication data are maintained.
- Backups are stored securely and tested for restore procedures.

10. Production Hardening
-----------------------
- Run behind a WSGI server (e.g., Gunicorn) with a reverse proxy (e.g., Nginx).
- Disable debug mode in production.
- Limit resource usage and concurrent operations.

=============================
END OF SECURITY POLICY
=============================
