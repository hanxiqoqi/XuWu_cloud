from flask import Flask, request, render_template, send_from_directory, redirect, url_for, session
import os
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 模拟用户数据库，添加存储使用情况
users = {}  # 格式: {username: {'password': '...', 'used_space': 0}}
TOTAL_SPACE = 10 * 1024 * 1024 * 1024  # 10G

@app.route('/')
def index():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)
    files = os.listdir(user_folder)
    used_space = users[username]['used_space']
    return render_template('index.html', files=files, used_space=used_space, total_space=TOTAL_SPACE)

# 尝试加载用户数据
try:
    with open('users.json', 'r') as f:
        users = json.load(f)
except FileNotFoundError:
    users = {}

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username in users:
            return '用户名已存在，请选择其他用户名。'
        users[username] = {'password': password, 'used_space': 0}
        # 保存用户数据到文件
        with open('users.json', 'w') as f:
            json.dump(users, f)
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"用户输入的用户名: {username}")
        print(f"用户输入的密码: {password}")
        if username in users:
            print(f"存储的密码: {users[username]['password']}")
        if username in users and users[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return '用户名或密码错误，请重试。'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    file = request.files['file']
    if file:
        file_size = len(file.read())
        file.seek(0)  # 重置文件指针
        if users[username]['used_space'] + file_size > TOTAL_SPACE:
            return '存储空间不足，请删除部分文件后再试。'
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
        file.save(os.path.join(user_folder, file.filename))
        users[username]['used_space'] += file_size
        return 'File uploaded successfully!'
    return 'No file provided!'

@app.route('/uploads/<username>/<filename>')
def uploaded_file(username, filename):
    if 'username' not in session or session['username'] != username:
        return redirect(url_for('login'))
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
    return send_from_directory(user_folder, filename)

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    username = session['username']
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], username)
    file_path = os.path.join(user_folder, filename)
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        os.remove(file_path)
        users[username]['used_space'] -= file_size
        return 'File deleted successfully!'
    else:
        return 'File not found!'

@app.template_filter('format_size')
def format_size_filter(bytes_size):
    if bytes_size >= 1024 ** 3:  # GB
        return f"{bytes_size / (1024 ** 3):.2f}GB"
    elif bytes_size >= 1024 ** 2:  # MB
        return f"{bytes_size / (1024 ** 2):.2f}MB"
    elif bytes_size >= 1024:  # KB
        return f"{bytes_size / 1024:.2f}KB"
    else:  # Bytes
        return f"{bytes_size}B"

# 公共网盘文件夹
PUBLIC_FOLDER = os.path.join(app.config['UPLOAD_FOLDER'], 'public')
if not os.path.exists(PUBLIC_FOLDER):
    os.makedirs(PUBLIC_FOLDER)

@app.route('/public_cloud')
def public_cloud():
    if 'username' not in session:
        return redirect(url_for('login'))
    files = os.listdir(PUBLIC_FOLDER)
    return render_template('public_cloud.html', files=files)

@app.route('/public_upload', methods=['POST'])
def public_upload_file():
    if 'username' not in session:
        return redirect(url_for('login'))
    file = request.files['file']
    if file:
        file.save(os.path.join(PUBLIC_FOLDER, file.filename))
        return 'File uploaded to public cloud successfully!'
    return 'No file provided!'

@app.route('/public_delete/<filename>', methods=['POST'])
def public_delete_file(filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    file_path = os.path.join(PUBLIC_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        return 'File deleted from public cloud successfully!'
    else:
        return 'File not found!'

@app.route('/public_download/<filename>')
def public_download(filename):
    if 'username' not in session:
        return redirect(url_for('login'))
    return send_from_directory(PUBLIC_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True, port=7788)
    