import json
import socket
import threading
import time
import requests

ip_lock = 0
log_lock = 0

# 目标服务器地址和端口
TARGET_HOST = "192.168.0.178"
TARGET_PORT = 8081
PROXY_PORT = 8888

# 日志服务器地址和端口
LOG_SERVER_HOST = "http://192.168.0.178:9090"
LOG_SERVER_URL = f"{LOG_SERVER_HOST}/log"

IP_SERVER_URL = f"{LOG_SERVER_HOST}/receive_ip"

class ReverseProxyHandler:
    def __init__(self, client_socket, target_host, target_port, log_server_url,ip_server_url,client_address):
        self.client_socket = client_socket
        self.target_host = target_host
        self.target_port = target_port
        self.log_server_url = log_server_url
        self.ip_server_url = ip_server_url
        self.client_address = client_address

    def handle(self):
        try:
            # 读取客户端请求，直到请求结束
            request_data = self.receive_data(self.client_socket)
            if not request_data:
                print("No data received from client, closing connection.")
                return

            print("Received request data, forwarding to log server.")
            # 将请求数据转发到日志服务器进行记录（只记录请求）
            self.forward_to_log_server("REQUEST", request_data)

            print("Forwarding request to backend server.")
            # 转发请求数据到目标服务器
            self.forward_request_to_backend(request_data)

            #记录客户端IP
            self.forward_ip_to_backend(self.client_address)

        except Exception as e:
            print(f"Error in handle method: {e}")
        finally:
            self.client_socket.close()

    def receive_data(self, client_socket):
        """读取客户端请求的完整数据"""
        request_data = b""
        while True:
            # 每次接收数据
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            request_data += chunk
            # 如果请求已经读取完毕，跳出循环（通常通过空行/Content-Length判断）
            if b"\r\n\r\n" in request_data or len(chunk) < 4096:
                break
        return request_data

    def forward_to_log_server(self, log_type, data):
        """将请求或响应数据转发到日志服务器"""
        try:
            # 禁用代理设置
            proxies = {
                'http': None,
                'https': None
            }

            # 获取当前时间戳
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())

            # 将日志数据结构化
            log_message = {
                "type": log_type,
                "timestamp": timestamp,
                "data": data.decode('utf-8')
            }

            # 设置请求头，明确数据为 JSON 格式
            headers = {"Content-Type": "application/json"}

            # 使用 `json=` 参数发送请求，requests 会自动转换为 JSON 格式
            response = requests.post(self.log_server_url, json=log_message, headers=headers, proxies=proxies)

            # 检查返回状态码
            if response.status_code != 200:
                print(f"[-] Error sending log data to log server: {response.status_code}")
            else:
                print(f"[+] Log successfully sent. Status Code: {response.status_code}")
        except Exception as e:
            print(f"[-] Error sending log data to log server: {e}")

    def forward_ip_to_backend(self, IP_DATA):
        """将完整的请求IP转发给目标服务器"""
        try:

            # 禁用代理设置
            proxies = {
                'http': None,
                'https': None
            }

            # 获取当前时间戳
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())

            # 将日志数据结构化
            ip_message = {
                "timestamp": timestamp,
                "data": IP_DATA
            }

            # 设置请求头，明确数据为 JSON 格式
            headers = {"Content-Type": "application/json"}
            # 使用 `json=` 参数发送请求，requests 会自动转换为 JSON 格式
            response = requests.post(self.ip_server_url, json=ip_message, headers=headers, proxies=proxies)
            # 检查返回状态码
            if response.status_code != 200:
                print(f"[-] Error sending ip data to log server: {response.status_code}")
            else:
                print(f"[+] ip successfully sent. Status Code: {response.status_code}")
        except Exception as e:
            print(f"[-] Error sending log data to log server: {e}")

    def forward_request_to_backend(self, request_data):
        """将完整的请求数据转发给目标服务器"""
        try:
            global log_lock
            log_lock = threading.Lock()
            # 连接到目标服务器
            backend_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            backend_socket.connect((self.target_host, self.target_port))

            # 转发请求数据
            backend_socket.sendall(request_data)

            # 从目标服务器接收响应数据
            response_data = self.receive_data(backend_socket)

            # 将响应数据返回给客户端
            self.client_socket.sendall(response_data)

            # 只记录响应（确保只记录一次）
            self.forward_to_log_server("RESPONSE", response_data)

        except Exception as e:
            self.client_socket.sendall(b"HTTP/1.1 500 Internal Server Error\r\n\r\n")
            print(f"Error while forwarding request: {e}")

        finally:
            backend_socket.close()


class ProxyServer:
    def __init__(self, host, port, target_host, target_port, log_server_url, ip_server_url):
        self.host = host
        self.port = port
        self.target_host = target_host
        self.target_port = target_port
        self.log_server_url = log_server_url
        self.ip_server_url = ip_server_url

    def start(self):
        # 创建代理服务器的 socket
        proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy_socket.bind((self.host, self.port))
        proxy_socket.listen(5)
        print(f"Proxy server started on {self.host}:{self.port}")


        while True:
            # 接受客户端连接
            client_socket, client_address = proxy_socket.accept()
            print(f"Client connected from {client_address}")

            # 处理客户端请求
            handler = ReverseProxyHandler(client_socket, self.target_host, self.target_port, self.log_server_url,self.ip_server_url,client_address)
            threading.Thread(target=handler.handle).start()


if __name__ == "__main__":
    # 设置目标服务器和日志服务器的地址和端口
    target_host = TARGET_HOST
    target_port = TARGET_PORT
    log_server_url = LOG_SERVER_URL
    ip_server_url = IP_SERVER_URL

    # 启动代理服务器
    proxy = ProxyServer("0.0.0.0", PROXY_PORT, target_host, target_port, log_server_url,ip_server_url)
    proxy.start()
