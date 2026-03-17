# 网页监控工具 - 精简版

监控网页内容变化，通过 OpenClaw 工具发送钉钉通知。

---

## 快速开始

### 1. 安装依赖

```bash
cd /home/admin/.openclaw/workspace/tix-monitor
pip3 install -r requirements.txt
```

### 2. 配置

**复制配置示例**：
```bash
cp config.yaml.example config.yaml
```

**编辑 `config.yaml`**，添加你的监控目标：
```yaml
targets:
  - name: "大麦网 - 演唱会"
    url: "https://www.damai.cn/yyj/"
    interval_seconds: 300
    keyword: "五月天"
```

**配置通知**：

本项目使用 [OpenClaw](https://github.com/openclaw) 工具发送钉钉通知。请确保：
1. 已安装 OpenClaw：`pip install openclaw`（或按 OpenClaw 文档安装）
2. 已配置好钉钉通知渠道
3. 在 `monitor.py` 中设置正确的 `NOTIFY_USER_ID`（钉钉会话 ID）

### 3. 运行

```bash
python3 monitor.py
```

---

## 配置说明

### config.yaml

```yaml
targets:
  - name: "监控名称"          # 必填，用于标识和通知
    url: "https://..."       # 必填，监控的 URL
    interval_seconds: 300    # 必填，检查间隔（秒）
    keyword: "关键词"         # 可选，只监控包含关键词的变化
    
settings:
  user_agent: "Mozilla/5.0..."  # 可选，默认 User-Agent
  timeout: 10                   # 可选，默认 10 秒
  logging: true                 # 可选，是否启用日志
```

### 环境变量

本项目通过代码配置通知方式（OpenClaw + 钉钉），无需额外环境变量。
如需修改通知目标，请编辑 `monitor.py` 中的 `NOTIFY_USER_ID` 常量。

---

## 文件结构

```
tix-monitor/
├── monitor.py          # 主程序
├── config.yaml         # 配置文件（自己创建）
├── config.yaml.example # 配置示例
├── requirements.txt    # Python 依赖
├── README.md           # 本文档
├── monitor.log         # 运行日志（自动生成）
└── data/
    └── state.json      # 监控状态（自动生成）
```

---

## 通知示例

```
🔔 网页变化提醒

名称：大麦网 - 演唱会
URL: https://www.damai.cn/yyj/
时间：2026-03-11 18:15:30

上次更新：2026-03-11 18:10:25
关键词：五月天
```

---

## 高级用法

### 后台运行

```bash
nohup python3 monitor.py > monitor.out 2>&1 &
```

### 查看日志

```bash
tail -f monitor.log
```

### 停止监控

```bash
pkill -f monitor.py
```

---

## 注意事项

1. **首次运行**只会保存基线，不会发送通知
2. **哈希变化**才会通知，避免重复
3. **关键词过滤**可以减少误报
4. **合理设置间隔**，避免过于频繁

---

## 故障排查

### 问题 1：抓取失败

检查网络连接和 URL 是否正确：
```bash
curl -I "https://www.damai.cn/yyj/"
```

### 问题 2：收不到通知

检查 OpenClaw 是否正确安装和配置：
```bash
# 测试 OpenClaw 是否可用
openclaw message send --channel dingtalk --target YOUR_CONVERSATION_ID --message "测试"
```

如果 OpenClaw 未安装，请参考 OpenClaw 文档进行安装配置。

### 问题 3：频繁误报

- 增加 `interval_seconds`
- 设置 `keyword` 过滤
- 检查网页是否有动态内容（广告、时间戳）
