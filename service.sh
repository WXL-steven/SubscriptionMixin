#!/bin/bash

# 启动 FastAPI 应用的脚本

# 设置环境变量，如果有的话
# export VARIABLE_NAME=value

# 激活 Python 环境
source /home/web-app/miniforge3/envs/sub/bin/activate

# 启动 Uvicorn 服务器
exec uvicorn main:app --host 127.0.0.1 --port 23334
