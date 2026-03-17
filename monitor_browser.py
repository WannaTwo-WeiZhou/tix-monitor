#!/usr/bin/env python3
"""
网页监控脚本 - 浏览器版本（用于动态网站如大麦网）
使用 Playwright 渲染 JavaScript 页面，获取真实票务数据
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

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("需要安装 playwright: pip install playwright")
    print("然后运行：playwright install")
    sys.exit(1)

import yaml

# ==================== 配置 ====================

# 钉钉 conversationId
NOTIFY_USER_ID = "1969522762692108"

# 文件路径
SCRIPT_DIR = Path(__file__).parent
STATE_FILE = SCRIPT_DIR / "data" / "state_browser.json"

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(SCRIPT_DIR / "monitor_browser.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


# ==================== 核心函数 ====================

def load_state():
    """加载状态文件"""
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}


def save_state(state):
    """保存状态文件"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def fetch_with_playwright(url, timeout=30000):
    """使用 Playwright 抓取网页（渲染 JavaScript）"""
    try:
        with sync_playwright() as p:
            # 启动浏览器（无头模式）
            browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
            page = browser.new_page(
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
            )
            
            # 设置超时
            page.set_default_timeout(timeout)
            
            # 访问页面
            logger.info(f"正在加载页面：{url[:80]}...")
            page.goto(url, wait_until="networkidle", timeout=timeout)
            
            # 等待页面完全加载（额外等待 2 秒确保动态内容加载）
            time.sleep(2)
            
            # 获取完整 HTML
            html = page.content()
            
            # 尝试提取关键票务信息
            ticket_info = extract_ticket_info(page, url)
            
            browser.close()
            
            return html, ticket_info
            
    except PlaywrightTimeout:
        logger.error(f"页面加载超时：{url}")
        return None, None
    except Exception as e:
        logger.error(f"浏览器抓取失败：{e}")
        return None, None


def extract_ticket_info(page, url):
    """从页面提取票务关键信息"""
    info = {}
    
    try:
        # 尝试提取常见票务元素
        selectors = {
            'price': ['[class*="price"]', '[class*="ticket"]', '.tm-price'],
            'status': ['[class*="status"]', '[class*="sell"]', '.tm-status'],
            'stock': ['[class*="stock"]', '[class*="inventory"]', '.tm-stock'],
        }
        
        # 获取页面文本
        text = page.inner_text("body")
        
        # 提取关键信息
        if any(kw in text for kw in ['缺货', '售罄', '已售完']):
            info['status'] = 'sold_out'
        elif any(kw in text for kw in ['可售', '有票', '购买']):
            info['status'] = 'available'
        elif any(kw in text for kw in ['预售', '预订']):
            info['status'] = 'presale'
        else:
            info['status'] = 'unknown'
        
        # 提取价格（简单匹配）
        import re
        prices = re.findall(r'¥\s*(\d+(?:\.\d+)?)', text)
        if prices:
            info['prices'] = sorted(set(prices))[:5]  # 最多 5 个价格
        
        info['text_length'] = len(text)
        info['timestamp'] = datetime.now().isoformat()
        
    except Exception as e:
        logger.warning(f"提取票务信息失败：{e}")
        info['error'] = str(e)
    
    return info


def compute_hash(content):
    """计算内容哈希"""
    if not content:
        return None
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def send_dingtalk_message(text, to_user=NOTIFY_USER_ID):
    """通过 OpenClaw message 工具发送钉钉通知"""
    cmd = [
        "openclaw", "message", "send",
        "--channel", "dingtalk",
        "--target", to_user,
        "--message", text
    ]
    
    try:
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


def check_target(name, url, state):
    """检查单个监控目标"""
    logger.info(f"检查：{name}")
    
    # 使用浏览器抓取
    html, ticket_info = fetch_with_playwright(url)
    
    if not html:
        logger.error(f"抓取失败：{name}")
        return
    
    # 计算哈希
    current_hash = compute_hash(html)
    if not current_hash:
        return
    
    # 获取上次状态
    target_id = f"{name}_{url}"
    last_hash = state.get(target_id, {}).get("hash")
    last_info = state.get(target_id, {}).get("ticket_info", {})
    
    # 首次抓取
    if not last_hash:
        logger.info(f"[{name}] 首次抓取，保存基线")
        logger.info(f"  票务状态：{ticket_info.get('status', 'unknown')}")
        if ticket_info.get('prices'):
            logger.info(f"  价格：{ticket_info['prices']}")
        state[target_id] = {
            "hash": current_hash,
            "ticket_info": ticket_info,
            "check_time": datetime.now().isoformat(),
            "url": url
        }
        save_state(state)
        return
    
    # 检查票务状态变化（只关心从缺货变为有票）
    current_status = ticket_info.get('status', 'unknown')
    last_status = last_info.get('status', 'unknown')
    
    # 只在有票时发送通知（从 sold_out 变为 available 或 presale）
    should_notify = False
    notify_reason = ""
    
    if last_status == 'sold_out' and current_status in ['available', 'presale']:
        should_notify = True
        notify_reason = f"🎫 余票状态：缺货 → {'有票' if current_status == 'available' else '预售'}"
    elif last_status == 'unknown' and current_status in ['available', 'presale']:
        # 首次检测到有票
        should_notify = True
        notify_reason = f"🎫 检测到有票！状态：{'有票' if current_status == 'available' else '预售'}"
    
    if should_notify:
        logger.warning(f"[{name}] {notify_reason}")
        current_prices = ticket_info.get('prices', [])
        
        # 发送通知
        notify_text = (
            f"🎉 有票提醒！\n\n"
            f"名称：{name}\n"
            f"URL: {url[:60]}...\n"
            f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"{notify_reason}\n"
            f"价格：{', '.join(['¥'+p for p in current_prices]) if current_prices else '暂无价格信息'}\n\n"
            f"快去抢购！🏃‍♂️"
        )
        
        send_dingtalk_message(notify_text)
    
    # 始终更新状态（无论是否通知）
    state[target_id]["hash"] = current_hash
    state[target_id]["ticket_info"] = ticket_info
    state[target_id]["check_time"] = datetime.now().isoformat()
    save_state(state)
    
    if not should_notify:
        logger.info(f"[{name}] 无余票变化 (状态：{current_status})")


def run_monitor():
    """主监控循环"""
    # 监控目标配置
    targets = [
        {
            "name": "大麦网 - 演出详情",
            "url": "https://m.damai.cn/shows/item.html?itemId=1021197513737",
            "interval_seconds": 300  # 5 分钟
        },
    ]
    
    logger.info("=" * 50)
    logger.info("网页监控启动（浏览器版本）")
    logger.info(f"监控目标：{len(targets)} 个")
    logger.info(f"状态：{STATE_FILE}")
    logger.info(f"通知：钉钉 → {NOTIFY_USER_ID}")
    logger.info("=" * 50)
    
    state = load_state()
    
    # 发送启动消息
    send_dingtalk_message(f"🤖 票务监控服务已启动（浏览器版本）\n时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    while True:
        try:
            for target in targets:
                check_target(target["name"], target["url"], state)
                
                interval = target.get("interval_seconds", 300)
                logger.debug(f"等待 {interval} 秒...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("监控已停止")
            break
        except Exception as e:
            logger.error(f"监控循环异常：{e}")
            time.sleep(10)


if __name__ == "__main__":
    run_monitor()
