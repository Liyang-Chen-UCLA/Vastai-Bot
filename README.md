# Vast.ai 实例监控 Telegram Bot

## 功能

- 🔔 **每日自动提醒** — 在你设定的时间自动检查实例，有运行中的立刻推送
- 🔍 **主动查询** — 随时发 `/status` 查看当前实例状态
- 🌍 **时区支持** — 自定义提醒时间和时区

---

## Bot 命令

| 命令 | 说明 |
|------|------|
| `/setkey <API_KEY>` | 设置 Vast.ai API Key |
| `/status` | 立即查询当前所有实例 |
| `/settime 09:00 Asia/Shanghai` | 设置每日提醒时间+时区 |
| `/reminder on\|off` | 开启/关闭自动提醒 |
| `/myconfig` | 查看当前配置 |

---

## 部署步骤

### 第一步：创建 Telegram Bot

1. 在 Telegram 搜索 `@BotFather`
2. 发送 `/newbot`，按提示设置名称
3. 获得 `BOT_TOKEN`（格式：`123456:ABCdef...`）

### 第二步：获取 Vast.ai API Key

1. 登录 [vast.ai](https://vast.ai)
2. 进入 Account → API Keys
3. 创建并复制 API Key

### 第三步：部署到 Railway（免费）

1. 将此项目上传到 GitHub（私有仓库即可）
2. 打开 [railway.app](https://railway.app) 并登录
3. 点击 **New Project → Deploy from GitHub repo**
4. 选择你的仓库
5. 进入 **Variables** 标签，添加环境变量：
   ```
   TELEGRAM_BOT_TOKEN = 你的Bot Token
   ```
6. 点击 Deploy，等待部署完成

### 第四步：开始使用

在 Telegram 找到你的 Bot，发送以下命令初始化：

```
/start
/setkey 你的Vast.ai_API_Key
/settime 09:00 Asia/Shanghai
/reminder on
```

---

## 常用时区参考

| 城市 | 时区字符串 |
|------|-----------|
| 北京/上海 | `Asia/Shanghai` |
| 香港 | `Asia/Hong_Kong` |
| 新加坡 | `Asia/Singapore` |
| 东京 | `Asia/Tokyo` |
| 纽约 | `America/New_York` |
| 伦敦 | `Europe/London` |

完整列表：https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

---

## 注意事项

- Railway 免费版每月有 500 小时运行时长，足够 Bot 使用
- API Key 存储在 Railway 服务器的本地文件中，建议使用只读权限的 API Key
- 如需多用户使用，每个人单独 `/setkey` 即可，数据互相隔离
