"""
财经新闻爬虫
抓取财联社 & 东方财富热点资讯
"""

import requests
from config import SOURCES


def fetch_finance():
    """抓取财联社财经快讯"""
    config = SOURCES["finance"]
    if not config["enabled"]:
        return []

    max_items = config["max_items"]
    news_list = []

    try:
        # 财联社电报 API (公开)
        url = "https://www.cls.cn/api/sw"
        params = {
            "app": "CailianpressWeb",
            "os": "web",
            "sv": "8.4.6",
            "sign": "",
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.cls.cn/telegraph",
        }

        # 先尝试财联社
        resp = requests.get(
            "https://www.cls.cn/nodeapi/updateTelegraphList",
            params={
                "app": "CailianpressWeb",
                "os": "web",
                "sv": "8.4.6",
                "rn": max_items,
                "category": "",
            },
            headers=headers,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        items = data.get("data", {}).get("roll_data", [])[:max_items]

        for item in items:
            title = item.get("title", "").strip()
            if not title:
                continue

            content = item.get("content", "").strip()
            ctime = item.get("ctime", 0)

            # 热度分数：基于时间新鲜度
            import time
            age_hours = (time.time() - ctime) / 3600 if ctime else 12
            score = max(3, min(10, int(10 - age_hours)))

            news_list.append({
                "title": title,
                "url": item.get("shareurl", f"https://www.cls.cn/detail/{item.get('id', '')}"),
                "source": "财经",
                "score": score,
                "comments": 0,
                "summary": content[:120] if content else title,
            })

        if not news_list:
            raise Exception("Empty response, trying fallback")

    except Exception as e:
        print(f"[Finance] 财联社失败: {e}, 尝试东方财富...")

        # 备用：东方财富热点
        try:
            url = "https://push2.eastmoney.com/api/qt/clist/get"
            params = {
                "pn": "1",
                "pz": str(max_items),
                "po": "1",
                "np": "1",
                "fltt": "2",
                "invt": "2",
                "fid": "f3",
                "fs": "m:0+t:6+f:!2,m:0+t:13+f:!2",  # 自选股热门
                "fields": "f2,f3,f4,f12,f14",
            }
            resp = requests.get(url, params=params, timeout=15)
            data = resp.json()

            items = data.get("data", {}).get("diff", [])[:max_items]
            for item in items:
                name = item.get("f14", "")
                code = item.get("f12", "")
                change = item.get("f3", 0)
                price = item.get("f2", 0)

                direction = "📈" if change > 0 else "📉" if change < 0 else "➡"
                title = f"{name} {direction}{change:+.2f}%"
                summary = f"股价: {price} | 涨跌幅: {change:+.2f}% | 代码: {code}"

                news_list.append({
                    "title": title,
                    "url": f"https://quote.eastmoney.com/{code}.html",
                    "source": "财经",
                    "score": min(10, max(3, abs(change) + 3)),
                    "comments": 0,
                    "summary": summary,
                })

        except Exception as e2:
            print(f"[Finance] 东方财富也失败: {e2}")

    print(f"[Finance] 抓取完成: {len(news_list)} 条")
    return news_list


if __name__ == "__main__":
    for n in fetch_finance()[:5]:
        print(f"  {n['title'][:60]}... | {n['summary'][:60]}")
