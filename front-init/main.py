import mimetypes
import urllib.parse
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import socket
import json
import threading
import os

BASE_DIR = Path()

STORAGE_DIR = Path("storage")
# Шлях до файлу даних
DATA_FILE = STORAGE_DIR / "data.json"

# Перевірка наявності папки зберігання та файлу даних
if not STORAGE_DIR.exists():
    # Якщо папка не існує, створити її
    STORAGE_DIR.mkdir(parents=True)

# Порт для HTTP сервера
HTTP_PORT = 3003
# Порт для UDP сервера
UDP_PORT = 5005

class GoitFramework(BaseHTTPRequestHandler):

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        print(route.query)
        match route.path:
            case '/':
                self.send_html('index.html')
            case '/contact':
                self.send_html('contact.html')
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        # Отримання даних з POST запиту
        post_data = self.rfile.read(content_length)
        # Вивід отриманих даних у консоль
        print("Received data:", post_data.decode())
        self.send_data_via_udp(post_data)
        # Відправлення клієнту відповіді з успішним статусом
        self.send_response(302)
        self.send_header('Location', '/index.html')
        self.end_headers()


    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())

    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-Type', mime_type)
        else:
            self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        with open(filename, 'rb') as file:
            data = file.read()
            if not self.wfile.closed:  # Перевірка, чи з'єднання не закрите
                self.wfile.write(data)
        
    def send_data_via_udp(self, data):
        # Створення UDP сокету
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            # Підключення до сервера (адреса і порт)
            server_address = ('localhost', UDP_PORT)
            # Відправка даних разом з часом отримання
            message = {'time': str(datetime.now()), 'data': data.decode()}
            message_bytes = json.dumps(message).encode()
            sock.sendto(message_bytes, server_address)
    
class HttpServerThread(threading.Thread):
    def __init__(self, host, port):
        super().__init__()
        self.host = host
        self.port = port

    def run(self):
        try:
            # Запуск HTTP сервера
            http_server = HTTPServer((self.host, self.port), GoitFramework)
            print(f"HTTP server is running on port {self.port}...")
            http_server.serve_forever()
        except KeyboardInterrupt:
            pass


class UdpServerThread(threading.Thread):
    def __init__(self):
        super().__init__()

    def run(self):
        try:
            # Запуск UDP сервера
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                # Призначення адреси і порту для сервера
                server_address = ('localhost', UDP_PORT)
                sock.bind(server_address)
                print("UDP server is running on port", UDP_PORT)
                # Обробка даних, отриманих від клієнтів
                while True:
                    data, _ = sock.recvfrom(4096)
                    # Розшифровка отриманих даних та збереження у файл JSON
                    try:
                        # Перевірка наявності файлу даних
                        decoded_data = json.loads(data.decode())
                        if os.path.exists(DATA_FILE):
                            with open(DATA_FILE, 'w') as file:
                                json.dump(decoded_data, file, indent=4)
                                file.write('\n')  # Додати роздільник між записами
                            print("Data saved successfully to data.json")
                    except json.JSONDecodeError as e:
                        print("Error decoding JSON data:", e)
        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    # Запуск HTTP сервера у окремому потоці
    http_server_thread = HttpServerThread('localhost', HTTP_PORT)
    http_server_thread.start()

    # Запуск UDP сервера у окремому потоці
    udp_server_thread = UdpServerThread()
    udp_server_thread.start()