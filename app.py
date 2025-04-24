from flask import Flask, render_template_string, send_from_directory, request, redirect, url_for, send_file
import os, qrcode, socket

app = Flask(__name__)
PORT = 5000
while True:
    folder_to_serve = input('Enter path to share (or press Enter for Downloads): ').strip()
    if not folder_to_serve:
        folder_to_serve = os.path.join(os.path.expanduser('~'), 'Downloads')
    if os.path.isdir(folder_to_serve):
        break
    print(f"Invalid path: {folder_to_serve}. Please try again.")

@app.route('/')
def index():
    files = os.listdir(folder_to_serve)
    files = [f for f in files if os.path.isfile(os.path.join(folder_to_serve, f))]

    html ='''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>File Upload</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', sans-serif; background-color: #1e1e1e; color: #ccc; display: flex; align-items: center; justify-content: center; height: 100dvh;">

    <div style="
        width: 90%;
        max-width: 800px;
        background-color: #2a2a2a;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 0 30px rgba(0,0,0,0.6);
        margin: 1rem;
    ">

        <!-- Files list -->
        <div style="flex: 1 1 100%; max-height: 70dvh; overflow-y: auto; border-radius: 6px 6px 0 0; background-color: #1a1a1a; padding: 1rem;">
            <h2 style="margin-top: 0; font-size: 1.2rem; color: #dadada;">Available Files</h2>
            <ul style="list-style: none; padding: 0; margin: 0;">
                {% for file in files %}
                    <li style="margin-bottom: 0.5rem;">
                        <a href="/files/{{ file }}" style="color: #66b2ff; text-decoration: none;">{{ file }}</a>
                    </li>
                {% endfor %}
            </ul>
        </div>

        <!-- Progress bar -->
        <div style="width: 100%;">
            <div style="width: 100%; background-color: #1a1a1a; height: 5px; border-radius: 0 0 8px 8px; overflow: hidden;">
                <div id="progressBar" style="height: 100%; width: 0%; background-color: #66bb6a; transition: width 0.3s;"></div>
            </div>
        </div>

        <!-- Upload section -->
        <div style="margin-top: 1rem;">
            <form id="uploadForm" style="width: 100%; display: flex;">
                <input type="file" id="fileInput" name="files" multiple required 
                    style="background-color: #333; color: #ccc; border: 1px solid #555; padding: 0.5rem; border-radius: 6px 0 0 6px; width: 70%;">
                <input type="button" value="Upload" onclick="uploadFiles()" 
                    style="background-color: darkgreen; color: white; border: none; padding: 0.6rem; font-size: 1rem; border-radius: 0 6px 6px 0; cursor: pointer; width: 30%;">
            </form>
        </div>

    </div>

    <script>
        function uploadFiles() {
            const input = document.getElementById('fileInput');
            const files = input.files;
            const progressBar = document.getElementById('progressBar');

            if (!files.length) {
                alert("Please select at least one file.");
                return;
            }

            let uploaded = 0;
            const totalFiles = files.length;

            const uploadNext = (index) => {
                if (index >= totalFiles) {
                    progressBar.style.width = "100%";
                    setTimeout(() => location.reload(), 1000);
                    return;
                }

                const file = files[index];
                const formData = new FormData();
                formData.append('file', file);

                const xhr = new XMLHttpRequest();
                xhr.open('POST', '/upload', true);

                xhr.onload = () => {
                    if (xhr.status === 200) {
                        uploaded++;
                        const progress = (uploaded / totalFiles) * 100;
                        progressBar.style.width = progress + "%";
                        uploadNext(index + 1);
                    } else {
                        alert('Failed to upload: ' + file.name);
                        uploadNext(index + 1);
                    }
                };

                xhr.onerror = () => {
                    alert('Error uploading: ' + file.name);
                    uploadNext(index + 1);
                };

                xhr.send(formData);
            };

            uploadNext(0);
        }
    </script>
</body>
</html>
     
    '''
    return render_template_string(html, files=files)

@app.route('/files/<path:filename>')
def serve_file(filename):
    file_path = os.path.join(folder_to_serve, filename)
    return send_file(file_path, as_attachment=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    filepath = os.path.join(folder_to_serve, file.filename)
    file.save(filepath)
    return redirect(url_for('index'))

def show_qr_terminal(value):
    qr = qrcode.QRCode(1,qrcode.constants.ERROR_CORRECT_L,  10,  2)
    qr.add_data(value)
    qr.make(fit=True)
    qr_matrix = qr.get_matrix()
    for row in qr_matrix:
        for col in row:
            print('\u2588'*2,end='') if col else print('  ',end='')
        print()

def get_ipaddr():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]

if __name__ == '__main__':
    ip=get_ipaddr()
    show_qr_terminal(f'http://{ip}:{PORT}')
    app.run(host='0.0.0.0', port=PORT)
