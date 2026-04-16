# Vast.ai 实例监控 Telegram Bot

## 功能

- 🔔 **每日自动提醒** — 在你设定的时间自动检查实例，有运行中的立刻推送
- 🔍 **主动查询** — 随时发 `/status` 查看当前实例状态
- 🌍 **时区支持** — 自定义提醒时间和时区
- 💾 **数据持久化** — 通过 Railway Volume 保存设置，重启不丢失
- 🏃 **保活机制** — 内置 Health Server，配合 cron-job.org 防止免费版休眠

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

1. Telegram 搜索 `@BotFather`
2. 发送 `/newbot`，按提示设置名称
3. 获得 Token，格式：`7123456789:AAFxxx...`，**保存好**

---

### 第二步：获取 Vast.ai API Key

1. 登录 [vast.ai](https://vast.ai)
2. 进入 **Account → API Keys**
3. 创建并复制 API Key

---

### 第三步：上传代码到 GitHub

1. 注册 [github.com](https://github.com)
2. 创建一个**私有仓库（Private）**
3. 将以下文件上传到仓库根目录：
   ```
   bot.py
   requirements.txt
   railway.toml
   README.md
   ```

---

### 第四步：部署到 Railway

1. 打开 [railway.app](https://railway.app)，用 GitHub 账号登录
2. 点击 **New Project → Deploy from GitHub repo**
3. 若搜索不到仓库，点击 **Configure GitHub App**，在 GitHub 授权页面将仓库加入访问列表
4. 选择仓库后，进入服务页面

**添加环境变量：**
- 点击 **Variables → Add Variable**
- 填入：
  ```
  TELEGRAM_BOT_TOKEN = 你第一步获得的Token
  ```

**添加 Volume（数据持久化）：**
- 点击 **Volumes → Add Volume**
- Mount Path 填：
  ```
  /app/data
  ```
- 点击保存，Railway 会自动重新部署

等待 1～2 分钟，部署完成。

---

### 第五步：防止免费版休眠

Railway 免费版无流量时会休眠，导致定时提醒失效。

1. 在 Railway 服务页面 → **Settings → Networking → Generate Domain**
   获得类似：`https://vastai-bot-xxx.up.railway.app`

2. 注册 [cron-job.org](https://cron-job.org)（免费）

3. 创建新任务：
   - URL 填你的 Railway 域名
   - 执行频率：**每 10 分钟**
   - 保存并启用

---

### 第六步：初始化 Bot

在 Telegram 找到你的 Bot，发送以下命令：

```
/start
/setkey 你的Vast.ai_API_Key
/settime 09:00 Asia/Singapore
/reminder on
```

完成！之后电脑关机也能正常收到提醒。

---

## 常用时区参考

| 城市 | 时区字符串 |
|------|-----------|
| 北京 / 上海 | `Asia/Shanghai` |
| 香港 | `Asia/Hong_Kong` |
| 新加坡 | `Asia/Singapore` |
| 东京 | `Asia/Tokyo` |
| 纽约 | `America/New_York` |
| 洛杉矶 / 西雅图 | `America/Los_Angeles` |
| 伦敦 | `Europe/London` |
| 悉尼 / 墨尔本 | `Australia/Sydney` |
| UTC | `UTC` |

完整列表：https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

---

## 注意事项

- Railway 免费版每月 500 小时，配合 cron-job.org 保活后可稳定运行
- API Key 存储在 Railway Volume 中，建议在 Vast.ai 创建**只读权限**的 API Key
- 多个用户可以共用同一个 Bot，每人单独 `/setkey` 即可，数据互相隔离