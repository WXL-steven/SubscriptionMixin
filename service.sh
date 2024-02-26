#!/bin/bash

# 启动 FastAPI 应用的脚本

# 设置环境变量，如果有的话
# export VARIABLE_NAME=value

# 激活 Python 环境
#source /home/web-app/miniforge3/envs/sub/bin/activate

# Modify to the directory of your FastAPI app
cd /home/web-app/app/SubscriptionMixin || exit

# 启动 Uvicorn 服务器
exec /home/web-app/miniforge3/envs/sub/bin/python -m uvicorn main:app --host 127.0.0.1 --port 23334
