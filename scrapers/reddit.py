"""
Reddit 热门新闻爬虫
使用 Reddit 公开 JSON API（无需认证）
抓取 r/worldnews, r/technology, r/science
"""

import requests
from config import SOURCES

SUBREDDITS = ["worldnews", "technology", "science"]


def fetch_reddit():
    """抓取 Reddit 多个子版块的热门新闻"""
    config = SOURCES["reddit"]
    if not config["enabled"]:
        return []

    max_items = config["max_items"]
    news_list = []

    headers = {
        "User-Agent": "NewsAggregator/1.0 (personal use; contact@example.com)"
    }

    for sub in SUBREDDITS:
        try:
            url = f"https://www.reddit.com/r/{sub}/hot.json?limit={max_items // len(SUBREDDITS) + 5}"
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            children = data.get("data", {}).get("children", [])
            for child in children:
                post = child.get("data", {})
                # 跳过固定帖和置顶帖
                if post.get("stickied"):
                    continue

                title = post.get("title", "")
                if not title:
                    continue

                permalink = post.get("permalink", "")
                news_list.append({
                    "title": title,
                    "url": f"https://www.reddit.com{permalink}" if permalink else "",
                    "source": f"Reddit r/{sub}",
                    "score": post.get("score", 0),
                    "comments": post.get("num_comments", 0),
                    "summary": post.get("selftext", "")[:200] if post.get("selftext") else "",
                })

        except Exception as e:
            print(f"[Reddit] r/{sub} 抓取失败: {e}")

    print(f"[Reddit] 抓取完成: {len(news_list)} 条")
    return news_list


if __name__ == "__main__":
    for n in fetch_reddit()[:5]:
        print(f"  {n['title'][:60]}... | {n['source']} | 热度:{n['score']}")
