from flask import Flask, render_template_string, send_from_directory, request, redirect, url_for, send_file
import os, qrcode, socket

app = Flask(__name__)
PORT = 5000
folder_to_serve = input('enter a path: ')
if not folder_to_serve: folder_to_serve = '/home/lappy/Downloads'

@app.route('/')
def index():
    files = os.listdir(folder_to_serve)
    files = [f for f in files if os.path.isfile(os.path.join(folder_to_serve, f))]
    f=open('index.html')
    html = f.read()
    legacy_html='''
                <body style="height: 100dvh;">
                    <h2>Availabe Files</h2>
                    {% for file in files %}
                        <li><a href="/files/{{ file }}">{{ file }}</a></li>
                    {% endfor %}
                    <h2>Upload a New File</h2>
                    <form action="/upload" method="POST" enctype="multipart/form-data">
                        <input type="file" name="file" required><br><br>
                        <input type="submit" value="Upload" onclick="this.style.display='none'">
                    </form>
                </body>
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
