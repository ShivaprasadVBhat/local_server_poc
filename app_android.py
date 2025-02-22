# app_android.py
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

# Configure to use Android Downloads folder
# On Android, the standard path to Downloads folder is /storage/emulated/0/Download
ANDROID_DOWNLOADS = '/storage/emulated/0/Download'
UPLOAD_FOLDER = os.path.join(ANDROID_DOWNLOADS, 'FileStorageAPI')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'csv', 'mp4', 'mp3'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 3000 * 1024 * 1024  # 3GB max file size

# Create uploads directory if it doesn't exist
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    print(f"[INFO] Storage directory set to: {UPLOAD_FOLDER}")
except Exception as e:
    print(f"[ERROR] Could not create storage directory at {UPLOAD_FOLDER}: {e}")
    print("[INFO] Trying fallback to current directory")
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    print(f"[INFO] Using fallback storage directory: {UPLOAD_FOLDER}")

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
        "storage_path": UPLOAD_FOLDER,
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
        try:
            file.save(file_path)
            
            # Return success response with file info
            return jsonify({
                "message": "File uploaded successfully",
                "filename": filename,
                "size": os.path.getsize(file_path),
                "path": file_path,
                "url": f"/api/files/{filename}"
            }), 201
        except Exception as e:
            return jsonify({"message": f"Error saving file: {str(e)}"}), 500
    
    return jsonify({"message": "File type not allowed"}), 400

# List all uploaded files
@app.route('/api/files', methods=['GET'])
@auth.login_required
def list_files():
    files = []
    try:
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(file_path):
                files.append({
                    "filename": filename,
                    "size": os.path.getsize(file_path),
                    "path": file_path,
                    "url": f"/api/files/{filename}"
                })
    except Exception as e:
        return jsonify({"message": f"Error listing files: {str(e)}"}), 500
    
    return jsonify({"files": files, "storage_path": UPLOAD_FOLDER})

# Download a file
@app.route('/api/files/<filename>', methods=['GET'])
@auth.login_required
def download_file(filename):
    try:
        return send_from_directory(
            app.config['UPLOAD_FOLDER'], 
            filename, 
            as_attachment=True
        )
    except Exception as e:
        return jsonify({"message": f"Error downloading file: {str(e)}"}), 500

# Delete a file
@app.route('/api/files/<filename>', methods=['DELETE'])
@auth.login_required
def delete_file(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Check if file exists
    if not os.path.exists(file_path):
        return jsonify({"message": "File not found"}), 404
    
    # Delete the file
    try:
        os.remove(file_path)
        return jsonify({"message": f"File {filename} deleted successfully"})
    except Exception as e:
        return jsonify({"message": f"Error deleting file: {str(e)}"}), 500

# Get storage info
@app.route('/api/storage', methods=['GET'])
@auth.login_required
def storage_info():
    try:
        # Get total size of all files
        total_size = 0
        file_count = 0
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
                file_count += 1
        
        return jsonify({
            "storage_path": UPLOAD_FOLDER,
            "file_count": file_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        })
    except Exception as e:
        return jsonify({"message": f"Error getting storage info: {str(e)}"}), 500

if __name__ == '__main__':
    # Setup credentials on startup
    setup_credentials()
    
    # Show storage location
    print(f"[INFO] Files will be stored in: {UPLOAD_FOLDER}")
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)