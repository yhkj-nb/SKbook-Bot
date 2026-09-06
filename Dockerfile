FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建数据目录
RUN mkdir -p data logs

# 配置环境变量
ENV WEB_HOST=0.0.0.0
ENV WEB_PORT=5200

EXPOSE 5200

CMD ["python3", "main.py"]