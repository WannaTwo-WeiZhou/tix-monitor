# 快速运行指南

## 1. 安装依赖

```bash
cd /home/admin/.openclaw/workspace/tix-monitor
pip3 install --user -r requirements.txt
```

## 2. 配置

### 编辑 config.yaml

```bash
cp config.yaml.example config.yaml
nano config.yaml
```

### 配置 OpenClaw 通知

本项目使用 OpenClaw 工具发送钉钉通知：

1. 安装 OpenClaw（如果尚未安装）：
```bash
pip install openclaw  # 或按 OpenClaw 文档安装
```

2. 配置钉钉通知渠道（参考 OpenClaw 文档）

3. 在 `monitor.py` 中设置 `NOTIFY_USER_ID` 为你的钉钉会话 ID

## 3. 运行

### 前台运行（测试用）

```bash
python3 monitor.py
```

### 后台运行（生产用）

```bash
nohup python3 monitor.py > monitor.out 2>&1 &
```

### 查看状态

```bash
# 查看进程
ps aux | grep monitor.py

# 查看日志
tail -f monitor.log

# 查看监控状态
cat data/state.json | python3 -m json.tool
```

## 4. 停止

```bash
pkill -f monitor.py
```

## 5. 测试通知

测试 OpenClaw 钉钉通知：

```bash
python3 -c "
from monitor import send_dingtalk_message
send_dingtalk_message('🔔 测试通知')
"
```

或直接测试 OpenClaw 命令：

```bash
openclaw message send --channel dingtalk --target YOUR_CONVERSATION_ID --message "测试"
```

---

## 示例配置

```yaml
targets:
  - name: "大麦网 - 五月天"
    url: "https://www.damai.cn/search?keyword=五月天"
    interval_seconds: 180  # 3 分钟
    keyword: "五月天"
    
  - name: "大麦网 - 周杰伦"
    url: "https://www.damai.cn/search?keyword=周杰伦"
    interval_seconds: 300  # 5 分钟
    keyword: "周杰伦"
```

---

## 故障排查

**抓取失败**：检查网络连接
```bash
curl -I https://www.damai.cn/
```

**收不到通知**：测试 OpenClaw
```bash
openclaw message send --channel dingtalk --target YOUR_CONVERSATION_ID --message "测试"
```
