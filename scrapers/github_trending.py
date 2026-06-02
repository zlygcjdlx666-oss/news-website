"""
GitHub Trending 仓库爬虫
抓取 GitHub Trending 页面，解析热门开源项目
"""

import requests
from bs4 import BeautifulSoup
from config import SOURCES


def fetch_github_trending():
    """抓取 GitHub Trending 今日热门仓库"""
    config = SOURCES["github_trending"]
    if not config["enabled"]:
        return []

    max_items = config["max_items"]
    news_list = []

    try:
        url = "https://github.com/trending?since=daily"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml",
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        repos = soup.select("article.Box-row")[:max_items]

        for repo in repos:
            try:
                # 仓库名
                h2 = repo.select_one("h2")
                if not h2:
                    continue
                repo_name = h2.get_text(strip=True).replace("\n", "").replace(" ", "")

                # 描述
                desc_el = repo.select_one("p")
                description = desc_el.get_text(strip=True) if desc_el else ""

                # 语言
                lang_el = repo.select_one("[itemprop='programmingLanguage']")
                language = lang_el.get_text(strip=True) if lang_el else "Unknown"

                # 今日 stars（从页面无法直接获取准确数字，用 star 总数代替）
                stars_el = repo.select_one(".d-inline-block.float-sm-right")
                stars = ""
                if stars_el:
                    stars = stars_el.get_text(strip=True)

                title = f"{repo_name} - {description}" if description else repo_name
                if language != "Unknown":
                    title += f" [{language}]"

                news_list.append({
                    "title": title[:200],
                    "url": f"https://github.com/{repo_name}",
                    "source": "GitHub Trending",
                    "score": 0,
                    "comments": 0,
                    "summary": f"热门开源项目 | 语言: {language} | Stars: {stars} | {description[:150]}",
                })

            except Exception:
                continue

    except Exception as e:
        print(f"[GitHub] 抓取失败: {e}")

    print(f"[GitHub] 抓取完成: {len(news_list)} 条")
    return news_list


if __name__ == "__main__":
    for n in fetch_github_trending()[:5]:
        print(f"  {n['title'][:60]}... | {n['source']}")
