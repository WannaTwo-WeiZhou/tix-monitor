#!/usr/env python3
"""
企业微信回调验证服务
用于验证企业微信的回调 URL 配置
"""

import hashlib
import logging
from flask import Flask, request, abort

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置（从 config.yaml 读取）
TOKEN = "bbCzviK5seiuSHGQMlumX"


def verify_signature(token, timestamp, nonce, echostr):
    """验证签名"""
    try:
        lst = [token, timestamp, nonce]
        lst.sort()
        sha = hashlib.sha1()
        for i in lst:
            sha.update(i.encode('utf-8'))
        hashvalue = sha.hexdigest()
        return hashvalue == request.args.get('msg_signature')
    except Exception as e:
        logger.error(f"验证失败：{e}")
        return False


@app.route('/wecom', methods=['GET', 'POST'])
def wecom_callback():
    """企业微信回调入口"""
    logger.info(f"收到请求：{request.method} {request.args}")
    
    # GET 请求：验证 URL
    if request.method == 'GET':
        msg_signature = request.args.get('msg_signature')
        timestamp = request.args.get('timestamp')
        nonce = request.args.get('nonce')
        echostr = request.args.get('echostr')
        
        logger.info(f"验证参数：signature={msg_signature}, ts={timestamp}, nonce={nonce}")
        
        if verify_signature(TOKEN, timestamp, nonce, echostr):
            logger.info("验证成功，返回 echostr")
            return echostr
        else:
            logger.warning("验证失败")
            abort(403)
    
    # POST 请求：接收消息（暂不处理）
    elif request.method == 'POST':
        logger.info("收到 POST 消息（暂不处理）")
        return "success"
    
    return "OK"


if __name__ == '__main__':
    logger.info("企业微信验证服务启动，监听端口 5001")
    app.run(host='0.0.0.0', port=5001)
