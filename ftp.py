from flask import Flask, render_template, send_file, url_for, request, redirect
import os
import urllib
import socket
import shutil
from psutil import disk_usage 
path = os.getcwd()

DOWNLOAD_DIR = f"{path}"

FTP_PORT = 8080

app = Flask(__name__, template_folder=f"{path}")

directory = DOWNLOAD_DIR

from time import time

# Get the hostname
hostname = socket.gethostname()

# Get the IPv4 address of the host
ip_address = socket.gethostbyname(hostname)

DOWNLOAD_INTERVAL = 30



SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']

def get_readable_file_size(size_in_bytes):
    if size_in_bytes is None:
        return '0B'
    index = 0
    while size_in_bytes >= 1024:
        size_in_bytes /= 1024
        index += 1
    try:
        return f'{round(size_in_bytes, 2)} {SIZE_UNITS[index]}'
    except IndexError:
        return 'File too large'
    
def get_files(path, sort_by='mtime'):
    """
    Returns a list of all files in the specified directory
    and its subdirectories, including their full paths,
    that are not currently being modified.
    """
    files = []
    current_time = time()
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            stat = os.stat(full_path)
            modified_time = stat.st_mtime if sort_by == 'mtime' else stat.st_ctime
            if (current_time - modified_time) > DOWNLOAD_INTERVAL:
                files.append((full_path, modified_time))
    return sorted(files, key=lambda x: x[1], reverse= True)


@app.route("/")
def list_files():
    total, used, free, disk = disk_usage('/')
    files = get_files(directory, sort_by='mtime')
    file_links = []
    file_names = []
    file_path = []
    file_size = []
    for file in files:
        file_path.append(file[0])
        encoded_filename = urllib.parse.quote(file[0])
        file_links.append(url_for('download_file', filename=encoded_filename))
        file_names.append(os.path.basename(file[0]))
        size = os.path.getsize(file[0])
        size = get_readable_file_size(size)
        file_size.append(size)
    Avail_Files = len(file_names)
    Avail_Storage = get_readable_file_size(free)
    data = zip(file_names, file_links, file_path, file_size)
    return render_template('index.html', data=data, Avail_Files = Avail_Files, Avail_Storage = Avail_Storage)

@app.route('/delete', methods=['POST'])
def delete_files():
    file_names = request.form.getlist('delete_file')
    for file_name in file_names:
        filepath = file_name
        if filepath.lower().startswith(directory.lower()):
            if os.path.isdir(filepath):
                shutil.rmtree(filepath)
            else:
                os.remove(filepath)
    return redirect(url_for('list_files'))

@app.route('/download/<path:filename>/')
def download_file(filename):
    decoded_filename = urllib.parse.unquote(filename)
    if os.name == 'nt':
        file_path = f"{decoded_filename}"
    # Windows-specific code here
    elif os.name == 'posix':
        file_path = f"/{decoded_filename}"
    # UNIX-specific code here
    if os.path.isfile(file_path):
        if file_path.lower().startswith(directory.lower()):
            return send_file(file_path, as_attachment=True)
        else:
            return "Forbidden: No Permission."
    else:
        return "Error: File not found."


app.run(host=ip_address, port=FTP_PORT)
