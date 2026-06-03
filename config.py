"""
配置文件 — 新闻聚合网站
从环境变量读取敏感信息（API Key），GitHub Actions 中通过 Secrets 设置
支持从 .env 文件加载（本地开发用）
"""

import os

# 尝试从 .env 文件加载环境变量
def _load_dotenv():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key not in os.environ:  # 不覆盖已有的环境变量
                        os.environ[key] = value

_load_dotenv()

# DeepSeek API 配置 (OpenAI 兼容格式)
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "your-api-key-here")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"  # DeepSeek-V3

# AI 处理参数
MAX_NEWS_TO_PROCESS = 200       # 每次最多处理的新闻数
TOP_NEWS_OUTPUT = 50            # 最终输出的精选新闻数
AI_TEMPERATURE = 0.3            # AI 温度（低=更稳定）
AI_MAX_TOKENS = 300             # 每条新闻摘要最大 token

# 新闻源配置
SOURCES = {
    "hackernews": {
        "enabled": True,
        "max_items": 30,
    },
    "reddit": {
        "enabled": True,
        "max_items": 30,
    },
    "bbc": {
        "enabled": True,
        "max_items": 30,
    },
    "github_trending": {
        "enabled": True,
        "max_items": 25,
    },
    "solidot": {
        "enabled": True,
        "max_items": 30,
    },
    "weibo": {
        "enabled": True,
        "max_items": 30,
    },
    "xkcd": {
        "enabled": True,
        "max_items": 5,
    },
    "producthunt": {
        "enabled": True,
        "max_items": 20,
    },
    "bilibili": {
        "enabled": True,
        "max_items": 20,
    },
    "steam": {
        "enabled": True,
        "max_items": 15,
    },
    "music": {
        "enabled": True,
        "max_items": 10,
    },
    "finance": {
        "enabled": True,
        "max_items": 15,
    },
}

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
