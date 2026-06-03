"""
AI 新闻处理器 — DeepSeek API
对抓取的新闻进行：去重筛选、重要性评分、中文摘要生成、分类标签
"""

import json
from openai import OpenAI
from config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    MAX_NEWS_TO_PROCESS,
    TOP_NEWS_OUTPUT,
    AI_TEMPERATURE,
)

CATEGORIES = ["科技", "财经", "国际", "科学", "产品", "社会", "娱乐", "趣闻", "其他"]

SYSTEM_PROMPT = f"""你是一个专业的新闻编辑，负责筛选和整理全球最有价值的每日新闻。

你的任务：
1. **去重筛选**：从输入新闻中去除重复、广告、低质量内容
2. **重要性评分**：综合信息价值和时效性，为每条新闻打分（1-10分）
3. **中文摘要**：用中文为每条新闻写一句精炼摘要（30-80字），涵盖核心信息
4. **分类标签**：为每条新闻打1-2个分类标签

分类标签可选：{", ".join(CATEGORIES)}

⚠️ 重要：必须保留约 5-8 条轻松有趣的内容（来自 XKCD、Product Hunt、B站热门等来源），
标记为"趣闻"分类。这些内容的作用是让读者在严肃新闻之间得到放松。
例如：有趣的漫画、新奇的产品、好玩的视频、脑洞大开的创意项目等。

只输出 JSON 数组，不要任何其他文字。
格式：[{{"id": 原序号, "title": "原标题(可微调为更清晰的中文)", "score": 8, "summary": "中文摘要", "categories": ["科技"]}}]
按重要性从高到低排序，但确保"趣闻"内容均匀穿插其中，最多返回 {TOP_NEWS_OUTPUT} 条。"""


def process_news(news_list, client=None):
    """
    使用 DeepSeek API 处理新闻列表

    Args:
        news_list: [{"title": "...", "url": "...", "source": "...", ...}, ...]
        client: OpenAI 客户端实例（可选，用于复用）

    Returns:
        [{"title": "...", "url": "...", "source": "...", "score": 8, "summary": "...", "categories": [...]}, ...]
    """
    if not news_list:
        print("[AI] 没有新闻需要处理")
        return []

    # 截取最多处理的条数
    if len(news_list) > MAX_NEWS_TO_PROCESS:
        # 按原始分数排序取 top
        news_list = sorted(news_list, key=lambda x: x.get("score", 0), reverse=True)
        news_list = news_list[:MAX_NEWS_TO_PROCESS]

    # 初始化客户端
    if client is None:
        client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
        )

    # 构建输入：给每条新闻编号
    input_text_lines = []
    for i, news in enumerate(news_list):
        score_info = f"热度:{news['score']}" if news.get("score") else ""
        comments_info = f"评论:{news['comments']}" if news.get("comments") else ""
        source_info = news.get("source", "")
        extra = " | ".join(filter(None, [score_info, comments_info]))
        line = f"[{i}] {news['title']} | 来源:{source_info}"
        if extra:
            line += f" | {extra}"
        if news.get("summary"):
            line += f" | 原文摘要:{news['summary'][:150]}"
        input_text_lines.append(line)

    input_text = "\n".join(input_text_lines)

    print(f"[AI] 输入 {len(news_list)} 条新闻，开始筛选...")

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            temperature=AI_TEMPERATURE,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"以下是今天抓取的 {len(news_list)} 条新闻，请筛选最重要的 {TOP_NEWS_OUTPUT} 条：\n\n{input_text}"},
            ],
            max_tokens=4096,
        )

        content = response.choices[0].message.content.strip()

        # 清理 JSON（模型偶尔会包裹 ```json）
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content[:-3]

        result = json.loads(content)

        # 合并回原始数据（URL 等字段）
        merged = []
        for item in result:
            idx = item.get("id", -1)
            if 0 <= idx < len(news_list):
                original = news_list[idx]
                merged.append({
                    "title": item.get("title", original["title"]),
                    "url": original.get("url", ""),
                    "source": original.get("source", ""),
                    "score": item.get("score", 5),
                    "summary": item.get("summary", ""),
                    "categories": item.get("categories", ["其他"]),
                    "original_score": original.get("score", 0),
                    "original_comments": original.get("comments", 0),
                })

        print(f"[AI] 筛选完成: {len(merged)} 条精选新闻")
        return merged

    except json.JSONDecodeError as e:
        print(f"[AI] JSON 解析失败: {e}")
        print(f"[AI] 原始响应: {content[:500]}...")

        # 降级：返回原始新闻带默认值
        fallback = []
        for i, n in enumerate(news_list[:TOP_NEWS_OUTPUT]):
            fallback.append({
                "title": n["title"],
                "url": n.get("url", ""),
                "source": n.get("source", ""),
                "score": 5,
                "summary": n.get("summary", n["title"])[:150],
                "categories": ["其他"],
                "original_score": n.get("score", 0),
                "original_comments": n.get("comments", 0),
            })
        return fallback

    except Exception as e:
        print(f"[AI] API 调用失败: {e}")
        return []


def generate_commentary(news_list, client=None):
    """
    基于今日新闻生成一段 AI 锐评

    Args:
        news_list: 已处理的新闻列表
        client: OpenAI 客户端实例（可选）

    Returns:
        str: 200-400字的每日锐评，或 None（失败时）
    """
    if not news_list:
        return None

    # 取前15条最重要新闻作为素材
    top_news = sorted(news_list, key=lambda x: x.get("score", 0), reverse=True)[:15]
    summaries = "\n".join(
        f"- [{n['source']}] {n['title']}：{n['summary']}" for n in top_news
    )

    prompt = f"""你是一个非常有个性的新闻评论员"磊哥"，风格犀利幽默、一针见血。

以下是今天最重要的新闻：

{summaries}

请写一段 200-350 字的"磊哥锐评"，要求：
1. 挑 2-3 条最值得关注的新闻点评
2. 有态度、有观点，不要复述新闻
3. 语言口语化、有网感，像跟朋友聊天
4. 可以在结尾给一个"今日金句"

直接输出锐评文字，不要加标题或署名。"""

    if client is None:
        client = OpenAI(
            api_key=DEEPSEEK_API_KEY,
            base_url=DEEPSEEK_BASE_URL,
        )

    try:
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            temperature=0.9,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
        )
        commentary = response.choices[0].message.content.strip()
        print(f"[AI] 锐评生成成功 ({len(commentary)} 字)")
        return commentary
    except Exception as e:
        print(f"[AI] 锐评生成失败: {e}")
        return None


if __name__ == "__main__":
    # 测试：假数据
    test_news = [
        {"title": "OpenAI announces GPT-5 with breakthrough reasoning", "url": "https://example.com/1", "source": "Hacker News", "score": 500, "comments": 200, "summary": ""},
        {"title": "全球气候峰会在巴黎召开，多国承诺减排目标", "url": "https://example.com/2", "source": "BBC News", "score": 0, "comments": 0, "summary": "World leaders gather..."},
        {"title": "New JavaScript framework released, developers excited", "url": "https://example.com/3", "source": "Hacker News", "score": 100, "comments": 50, "summary": ""},
        {"title": "某明星离婚案今日开庭", "url": "https://example.com/4", "source": "微博热搜", "score": 500000, "comments": 0, "summary": ""},
        {"title": "NASA discovers water on exoplanet in habitable zone", "url": "https://example.com/5", "source": "Reddit r/science", "score": 3000, "comments": 500, "summary": ""},
    ]
    results = process_news(test_news)
    for r in results:
        print(f"  [{r['score']}分] [{', '.join(r['categories'])}] {r['title'][:50]}...")
        print(f"    {r['summary'][:80]}...")
