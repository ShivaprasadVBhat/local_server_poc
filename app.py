# app_final.py
import os
import secrets
from flask import Flask, jsonify, request, send_from_directory, make_response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
CORS(app)
auth = HTTPBasicAuth()

# Configuration for file uploads
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Set simple credentials - change these if you want
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "password"

# Store credentials
users = {
    DEFAULT_USERNAME: generate_password_hash(DEFAULT_PASSWORD)
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None

# Save credentials to a file for reference
def setup_credentials():
    try:
        with open('credentials.txt', 'w') as f:
            f.write(f"Username: {DEFAULT_USERNAME}\n")
            f.write(f"Password: {DEFAULT_PASSWORD}\n")
        print(f"[INFO] Credentials saved to credentials.txt")
        print(f"[INFO] Username: {DEFAULT_USERNAME}")
        print(f"[INFO] Password: {DEFAULT_PASSWORD}")
    except Exception as e:
        print(f"[WARNING] Could not save credentials file: {e}")

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return jsonify({
        "message": "File Storage API is running!",
        "auth_required": True,
        "endpoints": {
            "ui": "/ui",
            "files": "/api/files"
        }
    })

# Serve the UI directly from the Flask app
@app.route('/ui')
def serve_ui():
    return send_from_directory('.', 'index.html')

# FILE HANDLING ENDPOINTS

# Upload a file
@app.route('/api/files', methods=['POST'])
@auth.login_required
def upload_file():
    # Check if a file was included in the request
    if 'file' not in request.files:
        return jsonify({"message": "No file part in the request"}), 400
    
    file = request.files['file']
    
    # Check if the user submitted an empty form
    if file.filename == '':
        return jsonify({"message": "No file selected"}), 400
    
    # Check if the file type is allowed
    if file and allowed_file(file.filename):
        # Secure the filename to prevent directory traversal attacks
        filename = secure_filename(file.filename)
        
        # Save the file to the upload folder
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Return success response with file info
        return jsonify({
            "message": "File uploaded successfully",
            "filename": filename,
            "size": os.path.getsize(file_path),
            "url": f"/api/files/{filename}"
        }), 201
    
    return jsonify({"message": "File type not allowed"}), 400

# List all uploaded files
@app.route('/api/files', methods=['GET'])
@auth.login_required
def list_files():
    files = []
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.isfile(file_path):
            files.append({
                "filename": filename,
                "size": os.path.getsize(file_path),
                "url": f"/api/files/{filename}"
            })
    
    return jsonify({"files": files})

# Download a file
@app.route('/api/files/<filename>', methods=['GET'])
@auth.login_required
def download_file(filename):
    return send_from_directory(
        app.config['UPLOAD_FOLDER'], 
        filename, 
        as_attachment=True
    )

# Delete a file
@app.route('/api/files/<filename>', methods=['DELETE'])
@auth.login_required
def delete_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Check if file exists
    if not os.path.exists(file_path):
        return jsonify({"message": "File not found"}), 404
    
    # Delete the file
    os.remove(file_path)
    
    return jsonify({"message": f"File {filename} deleted successfully"})

if __name__ == '__main__':
    # Setup credentials on startup
    setup_credentials()
    app.run(host='0.0.0.0', port=5000, debug=True)