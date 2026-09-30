# VoidShare

VoidShare is a small Flask app for uploading files and sharing them with expiring links.

## Requirements

- Python 3.10 or newer
- pip

## Install and run

1. Clone this repository and open a terminal in the project folder.
2. Create and activate a virtual environment:

   **Windows PowerShell**
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS/Linux**
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```sh
   python -m pip install -r requirements.txt
   ```

4. Set a private Flask session key (recommended):

   **Windows PowerShell**
   ```powershell
   $env:SECRET_KEY = (python -c "import secrets; print(secrets.token_hex(32))")
   ```

   **macOS/Linux**
   ```sh
   export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"
   ```

5. Start the development server:

   ```sh
   python app.py
   ```

6. Open http://127.0.0.1:5000 and create an account using Sign up.

The app creates data.json, users.json, and the UPLOADS folder locally when needed. These hold user accounts and uploaded content, so they are excluded from Git. Keep SECRET_KEY private and use a production WSGI server and HTTPS before exposing this development app to the internet.

## Configuration

- SECRET_KEY: Flask session signing key. If unset, a random key is generated for the current process.
- FLASK_DEBUG=1: enables Flask debug mode for local development. Debug mode is off by default.

## Project layout

- app.py: Flask application
- templates/: HTML templates
- static/: CSS and other static assets
- requirements.txt: Python packages installed with pip

## Publish this project on GitHub

1. Create an empty repository on GitHub. Do not add a README, license, or .gitignore there, since this folder already contains those files.
2. In this project folder, run the following commands and replace the URL with your repository URL:

   ```sh
   git init
   git add .
   git status
   git commit -m "Prepare VoidShare for GitHub"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
   git push -u origin main
   ```

Check `git status` before committing. The local `data.json`, `users.json`, and uploaded files are ignored so account details and private uploads are not published.
