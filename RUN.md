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

### 设置企业微信 Webhook

获取企业微信机器人 Webhook 后：

```bash
export WECOM_WEBHOOK="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=YOUR_KEY"
```

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

设置好 Webhook 后运行：

```bash
export WECOM_WEBHOOK="your-webhook-url"
python3 -c "
import os
os.environ['WECOM_WEBHOOK'] = os.getenv('WECOM_WEBHOOK')
from monitor import send_wechat_message
send_wechat_message('🔔 测试通知')
"
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

**收不到通知**：测试 Webhook
```bash
curl $WECOM_WEBHOOK \
  -H "Content-Type: application/json" \
  -d '{"msgtype":"text","text":{"content":"测试"}}'
```
