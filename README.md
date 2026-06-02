# 🌍 每日全球新闻精选

全自动新闻聚合网站 — 从全球多个来源抓取新闻，由 DeepSeek AI 智能筛选和总结，每日自动更新。

## 功能

- 📡 **6 个新闻源**：Hacker News、Reddit、BBC、GitHub Trending、知乎热榜、微博热搜
- 🤖 **AI 智能筛选**：DeepSeek 自动去重、评分、生成中文摘要、分类
- 🌐 **静态网站**：单页 HTML，支持深色/浅色模式、分类筛选、移动端响应式
- ⏰ **全自动**：GitHub Actions 每天定时运行，无需手动操作
- 💰 **几乎免费**：DeepSeek API 每月约 ¥1 元，GitHub + Vercel 完全免费

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置 API Key

```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="your-deepseek-api-key"

# Linux / macOS
export DEEPSEEK_API_KEY="your-deepseek-api-key"
```

> 在 [DeepSeek 开放平台](https://platform.deepseek.com) 获取 API Key

### 3. 运行

```bash
python main.py
```

运行后在浏览器中打开 `output/index.html` 查看。

### 4. 高级选项

```bash
python main.py --skip-ai          # 跳过 AI 筛选（测试用）
python main.py --source hackernews  # 只抓取指定来源
python main.py --debug            # 保存调试数据
```

## 部署到 Vercel

1. Fork 此仓库到你的 GitHub
2. 在 Vercel 中导入该仓库
3. 设置部署目录为 `output/`
4. 在 GitHub 仓库 Settings → Secrets 中添加 `DEEPSEEK_API_KEY`

之后每天自动更新，无需任何操作。

## 项目结构

```
新闻网站/
├── scrapers/              # 各新闻源爬虫
│   ├── hackernews.py      # Hacker News
│   ├── reddit.py          # Reddit
│   ├── bbc.py             # BBC News
│   ├── github_trending.py # GitHub Trending
│   ├── zhihu.py           # 知乎热榜
│   └── weibo.py           # 微博热搜
├── ai_processor.py        # DeepSeek AI 处理
├── generate_site.py       # 静态网站生成
├── main.py                # 主调度脚本
├── config.py              # 配置文件
├── .github/workflows/     # GitHub Actions
└── output/                # 生成的网站
```

## 技术栈

- Python 3.9+
- BeautifulSoup4 + requests（爬虫）
- DeepSeek API（AI 筛选/总结）
- GitHub Actions（定时任务）
- Vercel / GitHub Pages（部署）
