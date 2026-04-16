import os
import json
import asyncio
import logging
import requests
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Config paths ──────────────────────────────────────────────────────────────
DATA_FILE = Path("/app/data/settings.json")
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

# ── Health Server（防止 Railway 免费版休眠）────────────────────────────────────

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, *args):
        pass  # 静默日志


def start_health_server():
    server = HTTPServer(("0.0.0.0", 8080), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logger.info("Health server started on port 8080")


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_settings() -> dict:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text())
        except Exception:
            pass
    return {}


def save_settings(settings: dict):
    DATA_FILE.write_text(json.dumps(settings, indent=2))


def get_vast_instances(api_key: str) -> list:
    """Fetch running instances from Vast.ai API."""
    url = "https://console.vast.ai/api/v0/instances/"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("instances", [])
    except requests.exceptions.HTTPError as e:
        logger.error(f"Vast.ai API HTTP error: {e}")
        raise
    except Exception as e:
        logger.error(f"Vast.ai API error: {e}")
        raise


def format_instances(instances: list) -> str:
    """Format instance list into a readable message."""
    if not instances:
        return "✅ 当前没有运行中的实例，放心～"

    lines = [f"⚠️ 你有 *{len(instances)}* 个实例正在运行：\n"]
    for inst in instances:
        iid     = inst.get("id", "N/A")
        label   = inst.get("label") or "_(无标签)_"
        gpu     = inst.get("gpu_name", "Unknown GPU")
        gpu_num = inst.get("num_gpus", 1)
        cost_hr = round(float(inst.get("dph_total", 0) or 0), 4)

        # uptime
        start_ts = inst.get("start_date")
        if start_ts:
            started = datetime.utcfromtimestamp(float(start_ts))
            delta   = datetime.utcnow() - started
            hours   = int(delta.total_seconds() // 3600)
            minutes = int((delta.total_seconds() % 3600) // 60)
            uptime  = f"{hours}h {minutes}m"
        else:
            uptime = "未知"

        lines.append(
            f"🖥 *ID:* `{iid}`\n"
            f"   标签: {label}\n"
            f"   GPU: {gpu_num}× {gpu}\n"
            f"   运行时长: {uptime}\n"
            f"   费用: ${cost_hr}/hr\n"
        )

    total_cost = sum(round(float(i.get("dph_total", 0) or 0), 4) for i in instances)
    lines.append(f"💰 合计费率: *${round(total_cost, 4)}/hr*")
    return "\n".join(lines)


# ── Command Handlers ──────────────────────────────────────────────────────────

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id  = str(update.effective_chat.id)
    settings = load_settings()
    if chat_id not in settings:
        settings[chat_id] = {}
        save_settings(settings)

    text = (
        "👋 *Vast.ai 实例监控 Bot*\n\n"
        "可用命令：\n"
        "• `/setkey <API_KEY>` — 设置你的 Vast.ai API Key\n"
        "• `/status` — 立即查询当前实例\n"
        "• `/settime HH:MM <时区>` — 设置每日提醒时间\n"
        "  例：`/settime 09:00 Asia/Shanghai`\n"
        "  例：`/settime 22:00 America/New_York`\n"
        "• `/reminder on|off` — 开关自动提醒\n"
        "• `/myconfig` — 查看当前配置\n"
        "• `/help` — 显示帮助\n\n"
        "请先用 `/setkey` 设置 API Key。"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await cmd_start(update, ctx)


async def cmd_setkey(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not ctx.args:
        await update.message.reply_text(
            "用法：`/setkey <你的Vast.ai API Key>`", parse_mode="Markdown"
        )
        return

    api_key = ctx.args[0].strip()
    try:
        instances = get_vast_instances(api_key)
    except Exception:
        await update.message.reply_text("❌ API Key 无效或网络错误，请检查后重试。")
        return

    settings = load_settings()
    if chat_id not in settings:
        settings[chat_id] = {}
    settings[chat_id]["api_key"] = api_key
    save_settings(settings)

    await update.message.reply_text(
        f"✅ API Key 已保存！当前检测到 *{len(instances)}* 个实例。",
        parse_mode="Markdown",
    )


async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id  = str(update.effective_chat.id)
    settings = load_settings()
    api_key  = settings.get(chat_id, {}).get("api_key")

    if not api_key:
        await update.message.reply_text(
            "⚠️ 请先用 `/setkey <API_KEY>` 设置 API Key。", parse_mode="Markdown"
        )
        return

    await update.message.reply_text("🔍 查询中…")
    try:
        instances = get_vast_instances(api_key)
        await update.message.reply_text(format_instances(instances), parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ 查询失败：{e}")


async def cmd_settime(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if len(ctx.args) < 1:
        await update.message.reply_text(
            "用法：`/settime HH:MM <时区>`\n"
            "例：`/settime 09:00 Asia/Shanghai`\n"
            "例：`/settime 22:00 America/New_York`\n\n"
            "时区列表：https://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
            parse_mode="Markdown",
        )
        return

    time_str = ctx.args[0].strip()
    tz_str   = ctx.args[1].strip() if len(ctx.args) > 1 else "UTC"

    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        await update.message.reply_text(
            "❌ 时间格式错误，请用 HH:MM，例如 `09:00`", parse_mode="Markdown"
        )
        return

    try:
        ZoneInfo(tz_str)
    except (ZoneInfoNotFoundError, KeyError):
        await update.message.reply_text(
            f"❌ 时区 `{tz_str}` 无效，请参考 tz database 格式。", parse_mode="Markdown"
        )
        return

    settings = load_settings()
    if chat_id not in settings:
        settings[chat_id] = {}
    settings[chat_id]["remind_time"] = time_str
    settings[chat_id]["remind_tz"]   = tz_str
    settings[chat_id].setdefault("reminder_on", True)
    save_settings(settings)

    reschedule_all(ctx.application.bot)

    await update.message.reply_text(
        f"⏰ 已设置每日 *{time_str}* ({tz_str}) 自动提醒。\n"
        f"用 `/reminder on` 确保提醒已开启。",
        parse_mode="Markdown",
    )


async def cmd_reminder(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if not ctx.args or ctx.args[0].lower() not in ("on", "off"):
        await update.message.reply_text(
            "用法：`/reminder on` 或 `/reminder off`", parse_mode="Markdown"
        )
        return

    on = ctx.args[0].lower() == "on"
    settings = load_settings()
    if chat_id not in settings:
        settings[chat_id] = {}
    settings[chat_id]["reminder_on"] = on
    save_settings(settings)

    reschedule_all(ctx.application.bot)

    status = "已开启 ✅" if on else "已关闭 🔕"
    await update.message.reply_text(f"自动提醒{status}")


async def cmd_myconfig(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id  = str(update.effective_chat.id)
    settings = load_settings()
    user_cfg = settings.get(chat_id, {})

    has_key = "✅ 已设置" if user_cfg.get("api_key") else "❌ 未设置"
    r_time  = user_cfg.get("remind_time", "未设置")
    r_tz    = user_cfg.get("remind_tz", "UTC")
    r_on    = "开启 ✅" if user_cfg.get("reminder_on", False) else "关闭 🔕"

    await update.message.reply_text(
        f"*当前配置*\n\n"
        f"API Key：{has_key}\n"
        f"提醒时间：{r_time} ({r_tz})\n"
        f"自动提醒：{r_on}",
        parse_mode="Markdown",
    )


# ── Scheduler ─────────────────────────────────────────────────────────────────

scheduler = AsyncIOScheduler()


async def daily_check(chat_id: str, api_key: str, bot: Bot):
    logger.info(f"Running daily check for chat_id={chat_id}")
    try:
        instances = get_vast_instances(api_key)
        if instances:
            msg = f"⏰ *每日提醒*\n\n{format_instances(instances)}"
        else:
            msg = "⏰ *每日提醒*\n\n✅ 当前没有运行中的实例，一切正常～"
        await bot.send_message(chat_id=int(chat_id), text=msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"daily_check error for {chat_id}: {e}")
        try:
            await bot.send_message(chat_id=int(chat_id), text=f"❌ 定时检查失败：{e}")
        except Exception:
            pass


def reschedule_all(bot: Bot):
    """Remove all existing jobs and re-add from current settings."""
    for job in scheduler.get_jobs():
        job.remove()

    settings = load_settings()
    for chat_id, cfg in settings.items():
        if not cfg.get("reminder_on"):
            continue
        api_key = cfg.get("api_key")
        r_time  = cfg.get("remind_time")
        r_tz    = cfg.get("remind_tz", "UTC")

        if not api_key or not r_time:
            continue

        try:
            hour, minute = map(int, r_time.split(":"))
            tz = ZoneInfo(r_tz)
            scheduler.add_job(
                daily_check,
                trigger="cron",
                hour=hour,
                minute=minute,
                timezone=tz,
                args=[chat_id, api_key, bot],
                id=f"remind_{chat_id}",
                replace_existing=True,
            )
            logger.info(f"Scheduled daily check for {chat_id} at {r_time} {r_tz}")
        except Exception as e:
            logger.error(f"Failed to schedule for {chat_id}: {e}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    start_health_server()

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN environment variable")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start",    cmd_start))
    app.add_handler(CommandHandler("help",     cmd_help))
    app.add_handler(CommandHandler("setkey",   cmd_setkey))
    app.add_handler(CommandHandler("status",   cmd_status))
    app.add_handler(CommandHandler("settime",  cmd_settime))
    app.add_handler(CommandHandler("reminder", cmd_reminder))
    app.add_handler(CommandHandler("myconfig", cmd_myconfig))

    async def on_startup(application):
        reschedule_all(application.bot)
        if not scheduler.running:
            scheduler.start()
        logger.info("Bot started, scheduler running.")

    app.post_init = on_startup

    logger.info("Starting bot (polling mode)…")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()