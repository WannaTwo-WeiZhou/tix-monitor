#!/usr/bin/env python3
"""
网页监控脚本 - 最小可运行版本
功能：监控网页内容变化，通过 OpenClaw 消息工具通知
"""

import os
import sys
import time
import hashlib
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

import requests
import yaml

# ==================== 配置 ====================

# 钉钉 conversationId
NOTIFY_USER_ID = "1969522762692108"  # 周围的钉钉会话

# 文件路径
SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.yaml"
STATE_FILE = SCRIPT_DIR / "data" / "state.json"

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(SCRIPT_DIR / "monitor.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


# ==================== 核心函数 ====================

def load_config():
    """加载配置文件"""
    if not CONFIG_FILE.exists():
        logger.error(f"配置文件不存在：{CONFIG_FILE}")
        logger.info("请复制 config.yaml.example 为 config.yaml 并修改配置")
        sys.exit(1)
    
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    logger.info(f"已加载配置文件：{len(config.get('targets', []))} 个监控目标")
    logger.info(f"通知方式：钉钉 → {NOTIFY_USER_ID}")
    return config


def load_state():
    """加载状态文件"""
    if not STATE_FILE.exists():
        return {}
    
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"状态文件读取失败：{e}")
        return {}


def save_state(state):
    """保存状态文件"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    logger.debug(f"状态已保存：{STATE_FILE}")


def fetch_page(url, user_agent, timeout):
    """抓取网页内容"""
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logger.error(f"抓取失败 {url}: {e}")
        return None


def compute_hash(content):
    """计算内容哈希"""
    if not content:
        return None
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def filter_content(html, keyword=None):
    """
    过滤网页内容，提取关键部分
    如果有 keyword，只监控包含 keyword 的部分
    """
    if not html:
        return ""
    
    # 简单处理：移除脚本和样式
    import re
    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<[^>]+>", " ", html)  # 移除标签
    html = re.sub(r"\s+", " ", html).strip()  # 规范化空白
    
    # 如果有关键词，提取相关片段
    if keyword and keyword in html:
        # 提取关键词前后 200 字符
        idx = html.find(keyword)
        start = max(0, idx - 200)
        end = min(len(html), idx + 200)
        return html[start:end]
    
    # 返回前 1000 字符作为指纹
    return html[:1000]


def send_dingtalk_message(text, to_user=NOTIFY_USER_ID):
    """通过 OpenClaw message 工具发送钉钉通知"""
    cmd = [
        "openclaw", "message", "send",
        "--channel", "dingtalk",  # 指定钉钉渠道
        "--target", to_user,
        "--message", text
    ]
    
    try:
        # Python 3.6 兼容性：用 stdout/stderr 代替 capture_output
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                universal_newlines=True, timeout=30)
        if result.returncode == 0:
            logger.info(f"通知发送成功 (to: {to_user})")
            return True
        else:
            logger.error(f"通知发送失败：{result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error("通知发送超时")
        return False
    except Exception as e:
        logger.error(f"发送通知异常：{e}")
        return False


def check_target(target, state, config):
    """检查单个监控目标"""
    name = target.get("name", "未知")
    url = target.get("url")
    keyword = target.get("keyword")
    settings = target.get("settings", {})
    global_settings = config.get("settings", {})
    
    # 使用全局设置或覆盖
    user_agent = settings.get("user_agent", global_settings.get("user_agent", "Mozilla/5.0"))
    timeout = settings.get("timeout", global_settings.get("timeout", 10))
    
    logger.info(f"检查：{name}")
    
    # 抓取网页
    html = fetch_page(url, user_agent, timeout)
    if not html:
        return
    
    # 过滤内容
    content = filter_content(html, keyword)
    current_hash = compute_hash(content)
    
    if not current_hash:
        logger.warning(f"无法计算哈希：{name}")
        return
    
    # 获取上次哈希
    target_id = f"{name}_{url}"
    last_hash = state.get(target_id, {}).get("hash")
    last_check = state.get(target_id, {}).get("check_time")
    
    # 首次抓取：保存基线
    if not last_hash:
        logger.info(f"[{name}] 首次抓取，保存基线")
        state[target_id] = {
            "hash": current_hash,
            "check_time": datetime.now().isoformat(),
            "url": url
        }
        save_state(state)
        return
    
    # 检测变化
    if current_hash != last_hash:
        logger.warning(f"[{name}] 检测到变化！")
        
        # 发送通知
        notify_text = (
            f"🔔 网页变化提醒\n\n"
            f"名称：{name}\n"
            f"URL: {url}\n"
            f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"上次更新：{last_check or '未知'}\n"
            f"关键词：{keyword or '无'}"
        )
        
        send_dingtalk_message(notify_text)
        
        # 更新状态
        state[target_id]["hash"] = current_hash
        state[target_id]["check_time"] = datetime.now().isoformat()
        save_state(state)
    else:
        logger.info(f"[{name}] 无变化 (hash: {current_hash[:8]}...)")
        state[target_id]["check_time"] = datetime.now().isoformat()
        save_state(state)


def run_monitor():
    """主监控循环"""
    logger.info("=" * 50)
    logger.info("网页监控启动")
    logger.info(f"配置：{CONFIG_FILE}")
    logger.info(f"状态：{STATE_FILE}")
    logger.info(f"通知：钉钉 → {NOTIFY_USER_ID}")
    logger.info("=" * 50)
    
    state = load_state()
    
    while True:
        try:
            for target in CONFIG.get("targets", []):
                check_target(target, state, CONFIG)
                
                # 等待下一个目标的间隔时间
                interval = target.get("interval_seconds", 300)
                logger.debug(f"等待 {interval} 秒...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("监控已停止")
            break
        except Exception as e:
            logger.error(f"监控循环异常：{e}")
            time.sleep(10)


# ==================== 入口 ====================

if __name__ == "__main__":
    # 加载配置
    CONFIG = load_config()
    
    # 发送启动测试消息
    test_message = (
        f"🤖 网页监控服务已启动\n\n"
        f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"监控目标：{len(CONFIG.get('targets', []))} 个\n"
        f"配置：{CONFIG_FILE}\n\n"
        f"有任何变化将及时通知你。"
    )
    send_dingtalk_message(test_message)
    
    # 启动监控
    run_monitor()
