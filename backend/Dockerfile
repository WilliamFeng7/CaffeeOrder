# 使用轻量的 Python 镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 防止 Python 产生 pyc 文件，并让输出直接打印到终端
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 安装系统依赖 (使用阿里云镜像)
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖 (使用阿里云镜像)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 复制项目代码
COPY . .

# 暴露 80 端口
EXPOSE 80

# 启动命令 (使用 uvicorn)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
