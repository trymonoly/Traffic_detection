import json
import re
from functools import wraps

from flask import Flask, request, render_template, redirect, url_for, jsonify, session, flash

app = Flask(__name__)

LOG_FILE = "log/proxy_log.txt"  # 保存日志的文件
IP_FILE = "log/ip_log.txt"
user = {'id':'1','username': 'admin', 'password': 'admin'}
app.secret_key = 'your_secret_key'

# 鉴权装饰器，确保用户已登录
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))  # 如果未登录，重定向到登录页面
        return f(*args, **kwargs)  # 如果已登录，执行视图函数
    return decorated_function
def get_user_by_username(username):
    # 这里连接数据库并获取用户
    if username == user['username']:
        return user
    return None

def check_password_hash(password, hashed_password):
    if password == hashed_password:
        return True
    return False

#合并数据
def merge_request_response(request_dict, response_dict):
    # 从请求字典中获取时间戳
    timestamp = request_dict['timestamp']
    req = request_dict['data']
    # 从响应字典中提取数据，并简化为指定格式
    res = response_dict['data']
    # 合并为新的字典
    merged_dict = {
        'time': timestamp,
        'req': req,
        'res': res
    }
    return merged_dict

#解析IP数据
def parseIp(PATH):
    data_list = []
    with open(PATH, 'r') as file:
        # 初始化一个空字符串来构建完整的JSON对象
        json_str = ''
        for line in file:
            # 去除每行的首尾空白字符
            line = line.strip()
            # 如果行不为空，添加到json_str
            if line:
                json_str += line + ' '
            # 检查是否为完整的JSON对象
            if line.endswith('}'):
                try:
                    # 解析JSON字符串并添加到列表中
                    data_list.append(json.loads(json_str))
                    # 重置json_str为一个空字符串，为下一个JSON对象做准备
                    json_str = ''
                except json.JSONDecodeError:
                    # 如果解析失败，打印错误信息
                    print(f"Error decoding JSON from string: {json_str}")
    new_data_list = []
    for i in range(0,len(data_list),2):
        new_data_list.append(data_list[i])
    return new_data_list

#处理精简数据  存在问题
def process_logs():
    """处理日志和IP文件，并返回所需的日志数据"""
    data_list = parseIp(IP_FILE)
    datas = parseLog(LOG_FILE)
    log_data = []

    merged_data_list = []
    for i in range(0, len(datas), 2):
        if i + 1 < len(datas) and datas[i]['type'] == 'REQUEST' and datas[i + 1]['type'] == 'RESPONSE':
            merged_data = merge_request_response(datas[i], datas[i + 1])
            merged_data_list.append(merged_data)

    for i in range(0, len(data_list), 2):
        # 使用空格分割请求行
        parts = merged_data_list[i]['req'].split()
        # 确保请求方法和URI路径存在
        # 使用正则表达式提取URI部分
        print(data_list[i]['data'][0])
        print(merged_data_list[i]['req'][:3])
        print(merged_data_list[i]['time'])
        print(parts[1])
        new_dict = {
            "ip": data_list[i]['data'][0],
            "method": merged_data_list[i]['req'][:3],  # 获取请求方法
            "time": merged_data_list[i]['time'],
            "url": parts[1]
        }
        log_data.append(new_dict)

    return log_data

#解析请求数据
def parseLog(PATH):
    # 读取日志文件内容
    # 初始化一个空列表来存储数据
    datas = []

    # 打开文件并读取内容
    with open(PATH, 'r') as file:
        # 初始化一个空字符串来构建完整的JSON对象
        json_str = ''
        for line in file:
            # 去除每行的首尾空白字符
            line = line.strip()
            # 如果行不为空，添加到json_str
            if line:
                json_str += line + ' '
            # 检查是否为完整的JSON对象
            if line.endswith('}'):
                try:
                    # 解析JSON字符串并添加到列表中
                    datas.append(json.loads(json_str))
                    # 重置json_str为一个空字符串，为下一个JSON对象做准备
                    json_str = ''
                except json.JSONDecodeError:
                    # 如果解析失败，打印错误信息
                    print(f"Error decoding JSON from string: {json_str}")
        new_data_list = []
        for i in range(0, len(datas), 2):
            new_data_list.append(datas[i])
            new_data_list.append(datas[i+1])
    return new_data_list

#接收反向代理接收数据
@app.route('/log', methods=['POST'])
def receive_log():
    try:
        # 获取 POST 请求中的 JSON 数据
        log_data = request.get_json()

        # 打印日志数据
        print(f"Received log data:\n{json.dumps(log_data, indent=2)}")

        # 将日志数据保存到文件中
        with open(LOG_FILE, "a") as log_file:
            log_file.write(json.dumps(log_data, indent=2) + "\n\n")

        return "Log received", 200

    except Exception as e:
        return f"Error: {str(e)}", 400

#接收请求IP
@app.route('/receive_ip', methods=['POST'])
def receive_ip():
    try:
        # 获取 POST 请求中的 JSON 数据
        log_data = request.get_json()

        # 将日志数据保存到文件中
        with open(IP_FILE, "a") as log_file:
            log_file.write(json.dumps(log_data, indent=2) + "\n\n")

        return "Log received", 200

    except Exception as e:
        return f"Error: {str(e)}", 400

#解析展示全部流量  存在问题
@app.route('/Full_flow', methods=['GET','POST'])
@login_required
def Full_flow():
    datas = parseLog(LOG_FILE)

    merged_data_list = []
    for i in range(0, len(datas), 2):
        if i + 1 < len(datas) and datas[i]['type'] == 'REQUEST' and datas[i + 1]['type'] == 'RESPONSE':
            merged_data = merge_request_response(datas[i], datas[i + 1])
            merged_data_list.append(merged_data)

    return render_template('Full_flow.html', data=merged_data_list)

#配置和启动反向代理器
@app.route('/Configure', methods=['GET','POST'])
@login_required
def Configure():
    return render_template('Configure.html')

#日志查看
@app.route('/read_log', methods=['GET', 'POST'])
@login_required
def read_log():
    page = request.args.get('page', default=1, type=int)  # 获取URL中的 page 参数，如果没有则默认为 1
    log_data = process_logs()  # 从 session 获取 log_data

    if not log_data:
        return "No log data found", 404

    # 每页显示的条目数
    ITEMS_PER_PAGE = 10

    # 计算分页数据的开始和结束索引
    start = (page - 1) * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE

    # 获取当前页的数据
    logs = log_data[start:end]

    # 计算总页数
    total_pages = (len(log_data) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    return render_template('read_log.html', logs=logs, current_page=page, total_pages=total_pages)


#系统主页
@app.route('/', methods=['GET'])
def index():
    return render_template('login.html')

#系统登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # 获取用户提交的用户名和密码
        username = request.form['username']
        password = request.form['password']

        # 从数据库中查找该用户名的用户（这里使用假设的 get_user_by_username 函数）
        user = get_user_by_username(username)  # 假设返回的是一个包含 'username' 和 'password_hash' 的字典

        if user and check_password_hash(user['password'], password):
            # 如果用户存在且密码匹配，设置 session
            session['user_id'] = user['id']
            session['username'] = user['username']

            # 登录成功后重定向到 'read_log' 路由
            return redirect(url_for('read_log'))
        else:
            # 登录失败，显示错误信息
            flash('用户名或密码错误', 'danger')
            return redirect(url_for('login'))

        # 如果是 GET 请求，显示登录表单
    return render_template('login.html')


@app.route('/logout')
def logout():
    """
    登出路由：清除 session 中的用户登录信息，并重定向到登录页面
    """
    # 清除 session 中的用户信息
    session.pop('username', None)

    # 重定向到登录页面
    return redirect(url_for('login'))


if __name__ == "__main__":
    # 启动 Flask 服务器
    app.run(host="0.0.0.0", port=9090)
