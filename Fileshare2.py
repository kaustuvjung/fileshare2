from flask import Flask, render_template_string, request, send_file
from werkzeug.utils import secure_filename
import os
import qrcode
import socket
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB limit
PORT = 4000

# Get folder path with validation
while True:
    folder_to_serve = input('Enter path to share (or press Enter for Downloads): ').strip()
    if not folder_to_serve:
        folder_to_serve = os.path.join(os.path.expanduser('~'), 'Downloads')
    if os.path.isdir(folder_to_serve):
        break
    print(f"Invalid path: {folder_to_serve}. Please try again.")

@app.route('/')
def index():
    files = []
    try:
        files = [f for f in os.listdir(folder_to_serve) 
                if os.path.isfile(os.path.join(folder_to_serve, f))]
    except Exception as e:
        print(f"Error listing files: {e}")

    html = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>File Share</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0; padding: 0;
            font-family: 'Segoe UI', sans-serif;
            background: #1e1e1e; color: #ccc;
            display: flex; justify-content: center; align-items: center;
            min-height: 100vh;
        }
        .container {
            width: 95%; max-width: 800px;
            background: #2a2a2a; padding: 1.5rem;
            border-radius: 8px; box-shadow: 0 0 20px rgba(0,0,0,0.5);
            margin: 1rem;
        }
        .files-container {
            max-height: 60vh; overflow-y: auto;
            background: #1a1a1a; padding: 1rem;
            margin-bottom: 1rem; border-radius: 6px;
        }
        .file-item {
            display: flex; justify-content: space-between;
            padding: 0.5rem 0; border-bottom: 1px solid #333;
        }
        .file-link {
            color: #4dabf7; text-decoration: none;
            flex-grow: 1; word-break: break-all;
        }
        .file-size { color: #aaa; font-size: 0.8rem; }
        .progress-container {
            width: 100%; height: 6px;
            background: #1a1a1a; border-radius: 3px;
            margin-bottom: 1rem; overflow: hidden;
        }
        #progressBar {
            height: 100%; width: 0%;
            background: linear-gradient(90deg, #51cf66, #2f9e44);
            transition: width 0.3s;
        }
        #uploadForm {
            display: flex; gap: 0.5rem;
            margin-bottom: 0.5rem;
        }
        #fileInput {
            flex-grow: 1; padding: 0.5rem;
            background: #333; color: #eee;
            border: 1px solid #444; border-radius: 4px;
        }
        #uploadBtn {
            background: #2b8a3e; color: white;
            border: none; padding: 0 1rem;
            border-radius: 4px; cursor: pointer;
        }
        #statusText {
            text-align: center; font-size: 0.9rem;
            color: #adb5bd; margin: 0.5rem 0;
        }
        h2 { margin-top: 0; color: #dee2e6; }
        .qr-info {
            text-align: center; color: #868e96;
            margin-top: 1rem; font-size: 0.8rem;
        }
    </style>
</head>
<body>
    <div class="container">
        <h2>📁 File Share</h2>
        <div class="files-container">
            {% if files %}
                {% for file in files %}
                <div class="file-item">
                    <a href="/files/{{ file }}" class="file-link">{{ file }}</a>
                    <span class="file-size">{{ get_file_size(file) }}</span>
                </div>
                {% endfor %}
            {% else %}
                <div style="color: #868e96;">No files found</div>
            {% endif %}
        </div>

        <div class="progress-container">
            <div id="progressBar"></div>
        </div>
        <div id="statusText">Select files to upload</div>

        <form id="uploadForm" enctype="multipart/form-data">
            <input type="file" id="fileInput" name="file" multiple required>
            <button type="button" id="uploadBtn" onclick="uploadFiles()">Upload</button>
        </form>

        <div class="qr-info">
            Scan QR code with your phone to access
        </div>
    </div>

    <script>
        function formatSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1048576) return (bytes/1024).toFixed(1) + ' KB';
            if (bytes < 1073741824) return (bytes/1048576).toFixed(1) + ' MB';
            return (bytes/1073741824).toFixed(1) + ' GB';
        }

        async function uploadFiles() {
            const input = document.getElementById('fileInput');
            const files = input.files;
            const progressBar = document.getElementById('progressBar');
            const statusText = document.getElementById('statusText');

            if (!files.length) {
                statusText.textContent = "Please select files first";
                statusText.style.color = "#ff6b6b";
                return;
            }

            // Calculate total size
            let totalSize = 0;
            for (const file of files) totalSize += file.size;
            statusText.textContent = `Uploading ${files.length} files (${formatSize(totalSize)})...`;
            statusText.style.color = "#adb5bd";

            // Process files sequentially
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                const formData = new FormData();
                formData.append('file', file);

                try {
                    await new Promise((resolve, reject) => {
                        const xhr = new XMLHttpRequest();
                        xhr.open('POST', '/upload', true);

                        xhr.upload.onprogress = (e) => {
                            if (e.lengthComputable) {
                                const percent = Math.round((e.loaded / e.total) * 100);
                                progressBar.style.width = percent + '%';
                                statusText.textContent = 
                                    `Uploading ${i+1}/${files.length}: ${file.name} (${percent}%)`;
                            }
                        };

                        xhr.onload = () => {
                            if (xhr.status === 200) resolve();
                            else reject(`Error: ${xhr.statusText}`);
                        };

                        xhr.onerror = () => reject('Network error');
                        xhr.send(formData);
                    });
                } catch (error) {
                    statusText.textContent = `Failed: ${file.name} - ${error}`;
                    statusText.style.color = "#ff6b6b";
                    return;
                }
            }

            statusText.textContent = "Upload complete! Refreshing...";
            statusText.style.color = "#51cf66";
            setTimeout(() => location.reload(), 1000);
        }
    </script>
</body>
</html>
'''
   
    def get_file_size(filename):
        try:
            size = os.path.getsize(os.path.join(folder_to_serve, filename))
            return format_size(size)
        except:
            return "N/A"
    
    def format_size(size):
        if size < 1024: return f"{size} B"
        if size < 1024**2: return f"{size/1024:.1f} KB"
        if size < 1024**3: return f"{size/(1024**2):.1f} MB"
        return f"{size/(1024**3):.1f} GB"

    return render_template_string(html, files=files, get_file_size=get_file_size)

@app.route('/files/<filename>')
def serve_file(filename):
    try:
        safe_name = secure_filename(filename)
        filepath = os.path.join(folder_to_serve, safe_name)
        if not os.path.isfile(filepath):
            return "File not found", 404
        return send_file(filepath, as_attachment=True)
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file selected', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'Empty filename', 400

    try:
        filename = secure_filename(file.filename)
        if not filename:
            return 'Invalid filename', 400
            
        filepath = os.path.join(folder_to_serve, filename)
        file.save(filepath)
        return '', 200
    except Exception as e:
        return f'Upload failed: {str(e)}', 500

def generate_qr(url):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    return qr.get_matrix()

def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('8.8.8.8', 80))
            return s.getsockname()[0]
    except:
        return '127.0.0.1'

if __name__ == '__main__':
    ip = get_local_ip()
    url = f'http://{ip}:{PORT}'
    
    print(f"\n🖥️  File Share Server Running: {url}")
    print("📲 Scan this QR code with your phone:\n")
    
    qr = generate_qr(url)
    for row in qr:
        print('  ' + ''.join('██' if module else '  ' for module in row))
    
    print("\nPress Ctrl+C to stop the server")
    app.run(host='0.0.0.0', port=PORT, threaded=True)