#!/usr/bin/env python3
"""
使用 OpenClaw 消息工具发送钉钉通知
"""

import subprocess
import sys

def send_notification(text):
    """通过 OpenClaw message 工具发送钉钉通知"""
    # 使用 openclaw message 命令发送
    cmd = [
        "openclaw", "message", "send",
        "--channel", "dingtalk",
        "--target", "1969522762692108",
        "--message", text
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"通知发送成功")
            return True
        else:
            print(f"通知发送失败：{result.stderr}")
            return False
    except Exception as e:
        print(f"发送异常：{e}")
        return False

if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "测试消息"
    send_notification(text)
