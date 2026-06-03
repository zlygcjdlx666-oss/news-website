"""
静态网站生成器
将 AI 处理后的新闻数据渲染为单页 HTML 网站
"""

import json
import os
from datetime import datetime, timedelta
from config import OUTPUT_DIR

# HTML 模板 — 内嵌 CSS 和 JS，单文件部署
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>磊哥新闻网 — {date_str}</title>
<style>
:root {{
    --bg: #f8f9fa;
    --card-bg: #ffffff;
    --text: #212529;
    --text-secondary: #6c757d;
    --border: #dee2e6;
    --accent: #2563eb;
    --accent-hover: #1d4ed8;
    --tag-bg: #e9ecef;
    --score-bg: #dbeafe;
    --score-text: #1e40af;
    --shadow: 0 1px 3px rgba(0,0,0,0.08);
    --shadow-hover: 0 4px 12px rgba(0,0,0,0.12);
    --gradient-start: #2563eb;
    --gradient-end: #7c3aed;
}}

[data-theme="dark"] {{
    --bg: #1a1b1e;
    --card-bg: #25262b;
    --text: #e9ecef;
    --text-secondary: #adb5bd;
    --border: #373a40;
    --accent: #60a5fa;
    --accent-hover: #93bbfd;
    --tag-bg: #373a40;
    --score-bg: #1e3a5f;
    --score-text: #93bbfd;
    --shadow: 0 1px 3px rgba(0,0,0,0.3);
    --shadow-hover: 0 4px 12px rgba(0,0,0,0.5);
}}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    transition: background 0.3s, color 0.3s;
}}

/* ---- Header ---- */
.header {{
    background: linear-gradient(135deg, var(--gradient-start), var(--gradient-end));
    color: #fff;
    padding: 40px 20px 50px;
    text-align: center;
    position: relative;
    overflow: hidden;
}}
.header::after {{
    content: '';
    position: absolute;
    bottom: -20px;
    left: 0;
    right: 0;
    height: 40px;
    background: var(--bg);
    border-radius: 50% 50% 0 0;
}}
.header h1 {{
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.5px;
}}
.header .date {{
    margin-top: 8px;
    font-size: 0.95rem;
    opacity: 0.9;
}}
.header .meta {{
    margin-top: 12px;
    font-size: 0.85rem;
    opacity: 0.75;
}}

/* ---- Controls ---- */
.controls {{
    max-width: 960px;
    margin: -10px auto 20px;
    padding: 0 20px;
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    align-items: center;
    justify-content: center;
    position: relative;
    z-index: 1;
}}

.filter-btn {{
    padding: 6px 16px;
    border-radius: 20px;
    border: 1.5px solid var(--border);
    background: var(--card-bg);
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 0.85rem;
    transition: all 0.2s;
    font-family: inherit;
}}
.filter-btn:hover, .filter-btn.active {{
    border-color: var(--accent);
    color: var(--accent);
    background: var(--score-bg);
}}
.theme-toggle {{
    margin-left: auto;
    padding: 6px 12px;
    border-radius: 20px;
    border: 1.5px solid var(--border);
    background: var(--card-bg);
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 0.85rem;
    transition: all 0.2s;
    font-family: inherit;
}}
.theme-toggle:hover {{ background: var(--tag-bg); }}

/* ---- News Grid ---- */
.container {{
    max-width: 960px;
    margin: 0 auto;
    padding: 0 20px 60px;
}}

.news-grid {{
    display: flex;
    flex-direction: column;
    gap: 12px;
}}

.news-card {{
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: var(--shadow);
    transition: all 0.25s;
    cursor: pointer;
    position: relative;
}}
.news-card:hover {{
    box-shadow: var(--shadow-hover);
    transform: translateY(-2px);
}}
.news-card.hidden {{ display: none; }}

/* ---- Modal ---- */
.modal-overlay {{
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0, 0, 0, 0.6);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
    animation: fadeIn 0.2s ease;
    padding: 20px;
}}
.modal-overlay.hidden {{ display: none; }}

@keyframes fadeIn {{
    from {{ opacity: 0; }}
    to {{ opacity: 1; }}
}}

.modal {{
    background: var(--card-bg);
    border-radius: 16px;
    max-width: 640px;
    width: 100%;
    max-height: 80vh;
    overflow-y: auto;
    padding: 32px;
    position: relative;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}}

.modal-close {{
    position: absolute;
    top: 16px;
    right: 20px;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: none;
    background: var(--tag-bg);
    color: var(--text-secondary);
    font-size: 1.2rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
}}
.modal-close:hover {{
    background: var(--border);
    color: var(--text);
}}

.modal-source {{
    display: inline-block;
    padding: 3px 12px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 12px;
}}

.modal-title {{
    font-size: 1.4rem;
    font-weight: 800;
    line-height: 1.4;
    margin-bottom: 16px;
    color: var(--text);
}}

.modal-meta {{
    display: flex;
    gap: 16px;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 20px;
}}

.modal-summary {{
    font-size: 1rem;
    line-height: 1.8;
    color: var(--text-secondary);
    margin-bottom: 24px;
    padding: 16px;
    background: var(--tag-bg);
    border-radius: 10px;
}}

.modal-link {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 10px 20px;
    background: var(--accent);
    color: #fff;
    text-decoration: none;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    transition: all 0.2s;
}}
.modal-link:hover {{
    background: var(--accent-hover);
    transform: translateY(-1px);
}}

.card-header {{
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
    margin-bottom: 8px;
}}

.source-tag {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    white-space: nowrap;
}}
.source-hn {{ background: #ff6600; color: #fff; }}
.source-reddit {{ background: #ff4500; color: #fff; }}
.source-bbc {{ background: #bb1919; color: #fff; }}
.source-github {{ background: #24292e; color: #fff; }}
.source-zhihu {{ background: #0066ff; color: #fff; }}
.source-weibo {{ background: #e6162d; color: #fff; }}
.source-xkcd {{ background: #96a8c8; color: #fff; }}
.source-ph {{ background: #da552f; color: #fff; }}
.source-bili {{ background: #fb7299; color: #fff; }}

.card-title {{
    font-size: 1.1rem;
    font-weight: 700;
    margin-bottom: 6px;
    line-height: 1.5;
}}
.card-title a {{
    color: var(--text);
    text-decoration: none;
}}
.card-title a:hover {{ color: var(--accent); }}

.card-summary {{
    font-size: 0.9rem;
    color: var(--text-secondary);
    margin-bottom: 10px;
    line-height: 1.6;
}}

.card-footer {{
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
}}

.score-badge {{
    display: flex;
    align-items: center;
    gap: 4px;
    background: var(--score-bg);
    color: var(--score-text);
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 0.78rem;
    font-weight: 700;
}}

.cat-tag {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    background: var(--tag-bg);
    color: var(--text-secondary);
    font-size: 0.73rem;
}}

/* ---- Empty State ---- */
.empty {{
    text-align: center;
    padding: 80px 20px;
    color: var(--text-secondary);
}}
.empty .icon {{ font-size: 3rem; margin-bottom: 16px; }}

/* ---- Footer ---- */
.footer {{
    text-align: center;
    padding: 30px 20px;
    color: var(--text-secondary);
    font-size: 0.8rem;
    border-top: 1px solid var(--border);
    margin-top: 20px;
}}

@media (max-width: 640px) {{
    .header h1 {{ font-size: 1.4rem; }}
    .header {{ padding: 30px 16px 40px; }}
    .news-card {{ padding: 14px 16px; }}
    .card-title {{ font-size: 1rem; }}
    .controls {{ gap: 6px; }}
    .filter-btn {{ padding: 5px 12px; font-size: 0.78rem; }}
}}
</style>
</head>
<body data-theme="light">

<div class="header">
    <h1>🌍 磊哥新闻网</h1>
    <div class="date">{date_str}</div>
    <div class="meta">由 AI 从 {source_count} 个新闻源中筛选 · 共 {total_news} 条精选</div>
</div>

<div class="controls" id="controls">
    <button class="filter-btn active" data-filter="all">全部</button>
    {filter_buttons}
    <button class="theme-toggle" id="themeToggle" title="切换深色/浅色模式">🌙 深色模式</button>
</div>

<div class="container">
    <div class="news-grid" id="newsGrid">
        {news_cards}
    </div>
    <div id="emptyMsg" class="empty" style="display:none;">
        <div class="icon">🔍</div>
        <p>没有匹配的新闻</p>
    </div>
</div>

<div class="footer">
    <p>🤖 数据由 DeepSeek AI 筛选整理 · 每日自动更新 · 新闻来源: {sources_list}</p>
</div>

<!-- 新闻详情弹窗 -->
<div class="modal-overlay hidden" id="modalOverlay">
    <div class="modal">
        <button class="modal-close" id="modalClose">✕</button>
        <span class="modal-source" id="modalSource"></span>
        <h2 class="modal-title" id="modalTitle"></h2>
        <div class="modal-meta">
            <span class="score-badge" id="modalScore"></span>
            <span id="modalCats"></span>
        </div>
        <div class="modal-summary" id="modalSummary"></div>
        <a class="modal-link" id="modalLink" href="#" target="_blank" rel="noopener">
            🔗 查看原文
        </a>
    </div>
</div>

<script>
// ---- 分类筛选 ----
const filterBtns = document.querySelectorAll('.filter-btn');
const cards = document.querySelectorAll('.news-card');
const emptyMsg = document.getElementById('emptyMsg');

filterBtns.forEach(btn => {{
    btn.addEventListener('click', () => {{
        filterBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const filter = btn.dataset.filter;
        let visible = 0;
        cards.forEach(card => {{
            if (filter === 'all' || card.dataset.categories.includes(filter)) {{
                card.classList.remove('hidden');
                visible++;
            }} else {{
                card.classList.add('hidden');
            }}
        }});
        emptyMsg.style.display = visible === 0 ? 'block' : 'none';
    }});
}});

// ---- 深色/浅色模式 ----
const themeToggle = document.getElementById('themeToggle');
const body = document.body;
const savedTheme = localStorage.getItem('news-theme') || 'light';
body.dataset.theme = savedTheme;
updateThemeButton(savedTheme);

themeToggle.addEventListener('click', () => {{
    const next = body.dataset.theme === 'light' ? 'dark' : 'light';
    body.dataset.theme = next;
    localStorage.setItem('news-theme', next);
    updateThemeButton(next);
}});

function updateThemeButton(theme) {{
    themeToggle.textContent = theme === 'light' ? '🌙 深色模式' : '☀️ 浅色模式';
}}

// ---- 卡片点击打开详情弹窗 ----
const modalOverlay = document.getElementById('modalOverlay');
const modalClose = document.getElementById('modalClose');
const modalSource = document.getElementById('modalSource');
const modalTitle = document.getElementById('modalTitle');
const modalScore = document.getElementById('modalScore');
const modalCats = document.getElementById('modalCats');
const modalSummary = document.getElementById('modalSummary');
const modalLink = document.getElementById('modalLink');

function openModal(card) {{
    const source = card.dataset.source;
    const title = card.dataset.title;
    const url = card.dataset.url;
    const score = card.dataset.score;
    const summary = card.dataset.summary;
    const cats = card.dataset.categories.split(',');
    const sourceCss = card.dataset.sourceCss;

    modalSource.textContent = source;
    modalSource.className = 'modal-source ' + sourceCss;
    modalTitle.textContent = title;
    modalScore.innerHTML = '⭐ ' + score + '分';
    modalCats.innerHTML = cats.map(c => '<span class="cat-tag">' + c + '</span>').join('');
    modalSummary.textContent = summary;
    modalLink.href = url;
    modalLink.style.display = url ? 'inline-flex' : 'none';
    modalOverlay.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}}

function closeModal() {{
    modalOverlay.classList.add('hidden');
    document.body.style.overflow = '';
}}

cards.forEach(card => {{
    card.addEventListener('click', (e) => {{
        if (e.target.tagName === 'A') return;
        openModal(card);
    }});
}});

modalClose.addEventListener('click', closeModal);
modalOverlay.addEventListener('click', (e) => {{
    if (e.target === modalOverlay) closeModal();
}});
document.addEventListener('keydown', (e) => {{
    if (e.key === 'Escape') closeModal();
}});
</script>
</body>
</html>'''

SOURCE_CSS_MAP = {
    "Hacker News": "source-hn",
    "Reddit": "source-reddit",
    "BBC": "source-bbc",
    "GitHub Trending": "source-github",
    "GitHub": "source-github",
    "Solidot": "source-zhihu",
    "微博热搜": "source-weibo",
    "微博": "source-weibo",
    "XKCD": "source-xkcd",
    "Product Hunt": "source-ph",
    "B站热门": "source-bili",
    "B站": "source-bili",
}


def get_source_css(source):
    """根据来源名称返回 CSS 类"""
    for key, css in SOURCE_CSS_MAP.items():
        if key in source:
            return css
    return "source-hn"


def generate_news_card(news, index):
    """生成单条新闻的 HTML 卡片"""
    title = news.get("title", "")
    url = news.get("url", "#")
    source = news.get("source", "")
    score = news.get("score", 0)
    summary = news.get("summary", "")
    categories = news.get("categories", ["其他"])
    cats_str = ",".join(categories)

    source_css = get_source_css(source)

    cat_tags = "".join(f'<span class="cat-tag">{c}</span>' for c in categories[:3])
    score_stars = "⭐" * min(10, max(1, score))

    return f'''<article class="news-card" data-categories="{cats_str}" data-url="{url}" data-source="{source}" data-title="{title}" data-score="{score}" data-summary="{summary}" data-source-css="{source_css}" style="animation-delay:{index * 0.03}s">
    <div class="card-header">
        <span class="source-tag {source_css}">{source}</span>
    </div>
    <h2 class="card-title">{title}</h2>
    <p class="card-summary">{summary}</p>
    <div class="card-footer">
        <span class="score-badge">{score_stars} {score}分</span>
        {cat_tags}
    </div>
</article>'''



def generate_site(news_list, output_dir=None):
    """
    生成静态网站

    Args:
        news_list: AI 处理后的新闻列表
        output_dir: 输出目录（默认使用 config 中的 OUTPUT_DIR）
    """
    if output_dir is None:
        output_dir = OUTPUT_DIR

    os.makedirs(output_dir, exist_ok=True)

    # 统计来源
    sources_set = set()
    for n in news_list:
        src = n.get("source", "").split(" r/")[0]
        sources_set.add(src)

    # 收集所有分类
    all_categories = set()
    for n in news_list:
        for c in n.get("categories", []):
            all_categories.add(c)

    # 生成筛选按钮
    cat_order = ["科技", "国际", "科学", "财经", "产品", "趣闻", "娱乐", "社会", "其他"]
    sorted_cats = [c for c in cat_order if c in all_categories]
    sorted_cats += [c for c in sorted(all_categories) if c not in cat_order]
    filter_buttons = "\n    ".join(
        f'<button class="filter-btn" data-filter="{c}">{c}</button>' for c in sorted_cats
    )

    # 生成新闻卡片
    news_cards = "\n        ".join(
        generate_news_card(n, i) for i, n in enumerate(news_list)
    )

    # 日期
    yesterday = datetime.now() - timedelta(days=1)
    date_str = f"{yesterday.strftime('%Y年%m月%d日')} 新闻汇总"

    # 来源列表
    sources_list = " · ".join(sorted(sources_set))

    # 填充模板
    html = HTML_TEMPLATE.format(
        date_str=date_str,
        source_count=len(sources_set),
        total_news=len(news_list),
        filter_buttons=filter_buttons,
        news_cards=news_cards,
        sources_list=sources_list,
    )

    # 写入文件
    output_path = os.path.join(output_dir, "index.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[生成] 网站已生成: {output_path}")
    print(f"[生成] 共 {len(news_list)} 条新闻, {len(sources_set)} 个来源")
    return output_path


if __name__ == "__main__":
    # 测试
    test_data = [
        {
            "title": "OpenAI 发布 GPT-5：推理能力实现重大突破",
            "url": "https://example.com/1",
            "source": "Hacker News",
            "score": 9,
            "summary": "OpenAI 正式发布 GPT-5 模型，在数学推理和代码生成方面比前代提升显著。",
            "categories": ["科技", "产品"],
            "original_score": 500,
            "original_comments": 200,
        },
        {
            "title": "全球气候峰会达成历史性减排协议",
            "url": "https://example.com/2",
            "source": "BBC News",
            "score": 8,
            "summary": "巴黎气候峰会上，196个国家承诺到2035年将碳排放减少60%。",
            "categories": ["国际", "科学"],
            "original_score": 0,
            "original_comments": 0,
        },
        {
            "title": "某明星官宣离婚",
            "url": "https://example.com/3",
            "source": "微博热搜",
            "score": 3,
            "summary": "知名艺人今日通过工作室发布离婚声明。",
            "categories": ["娱乐"],
            "original_score": 950000,
            "original_comments": 0,
        },
    ]
    generate_site(test_data)
    print("请在浏览器中打开 output/index.html 查看效果")
