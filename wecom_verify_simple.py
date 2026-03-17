#!/usr/bin/env python3
"""
简易企业微信回调验证服务（单文件，无依赖）
"""

import http.server
import socketserver
import hashlib
import urllib.parse
import logging

PORT = 5001
TOKEN = "bbCzviK5seiuSHGQMlumX"

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)


class WeComHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")
    
    def do_GET(self):
        """处理 GET 请求（验证 URL）"""
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        
        logger.info(f"收到验证请求：{params}")
        
        msg_signature = params.get('msg_signature', [''])[0]
        timestamp = params.get('timestamp', [''])[0]
        nonce = params.get('nonce', [''])[0]
        echostr = params.get('echostr', [''])[0]
        
        # 验证签名
        lst = sorted([TOKEN, timestamp, nonce])
        sha = hashlib.sha1()
        for i in lst:
            sha.update(i.encode('utf-8'))
        hashvalue = sha.hexdigest()
        
        if hashvalue == msg_signature:
            logger.info("✓ 验证成功")
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(echostr.encode('utf-8'))
        else:
            logger.warning(f"✗ 验证失败：期望 {hashvalue}, 收到 {msg_signature}")
            self.send_response(403)
            self.end_headers()
    
    def do_POST(self):
        """处理 POST 请求（接收消息）"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        logger.info(f"收到 POST 消息：{body[:200]}")
        
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'success')


if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), WeComHandler) as httpd:
        logger.info(f"企业微信验证服务运行在端口 {PORT}")
        logger.info(f"回调 URL: http://47.102.153.56:{PORT}/wecom")
        httpd.serve_forever()
