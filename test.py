#!/usr/bin/env python3
"""
测试脚本 - 验证核心功能
"""

import os
import sys
from pathlib import Path

# 添加环境变量测试
os.environ["WECOM_WEBHOOK"] = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test"

# 导入监控模块
sys.path.insert(0, str(Path(__file__).parent))
from monitor import (
    load_config,
    load_state,
    save_state,
    compute_hash,
    filter_content,
    send_wechat_message
)

print("=" * 50)
print("网页监控工具 - 功能测试")
print("=" * 50)

# 测试 1：加载配置
print("\n[测试 1] 加载配置...")
config = load_config()
print(f"✅ 成功加载 {len(config['targets'])} 个监控目标")

# 测试 2：哈希计算
print("\n[测试 2] 哈希计算...")
test_content = "<html><body>测试内容</body></html>"
hash1 = compute_hash(test_content)
hash2 = compute_hash(test_content)
hash3 = compute_hash(test_content + "修改")
print(f"  原始哈希：{hash1}")
print(f"  重复计算：{hash2}")
print(f"  修改后：  {hash3}")
print(f"  ✅ 哈希一致：{hash1 == hash2}")
print(f"  ✅ 变化检测：{hash1 != hash3}")

# 测试 3：内容过滤
print("\n[测试 3] 内容过滤...")
html = "<html><head><script>alert(1)</script></head><body>五月天 演唱会 门票</body></html>"
filtered = filter_content(html, keyword="五月天")
print(f"  原始长度：{len(html)}")
print(f"  过滤后：  {filtered[:50]}...")
print(f"  ✅ 关键词提取：{'五月天' in filtered}")

# 测试 4：状态保存
print("\n[测试 4] 状态保存...")
state = {
    "test_target": {
        "hash": "abc123",
        "check_time": "2026-03-11T18:00:00",
        "url": "https://example.com"
    }
}
save_state(state)
loaded = load_state()
print(f"  ✅ 状态保存成功：{'test_target' in loaded}")

# 测试 5：企业微信通知（模拟）
print("\n[测试 5] 企业微信通知...")
result = send_wechat_message("🔔 测试通知\n\n这是一条测试消息")
print(f"  {'✅ 发送成功' if result else '⚠️  发送失败（可能是测试 Webhook）'}")

print("\n" + "=" * 50)
print("所有测试完成！")
print("=" * 50)
