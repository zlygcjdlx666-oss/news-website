"""
CS:GO 皮肤大盘指数 — 抓取自 firepulse.com.cn
FirePulse 是百万 CS2 玩家使用的饰品行情平台
"""

import requests
from config import SOURCES

FIREPULSE_API = "https://api.firepulse.com.cn/v1/market/facade/wiki/market_index_list"


def fetch_csgo_market():
    """从 FirePulse 抓取 CS:GO 大盘指数"""
    config = SOURCES.get("csgo", {})
    if not config.get("enabled", True):
        return []

    max_items = config.get("max_items", 15)
    news_list = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://firepulse.com.cn/",
        }
        resp = requests.get(FIREPULSE_API, headers=headers, timeout=15)
        data = resp.json()

        if data.get("code") != 200:
            raise Exception(f"API错误: {data.get('message', 'unknown')}")

        items = data.get("data", [])[:max_items]
        if not items:
            raise Exception("返回空数据")

        total_price = 0
        total_volume = 0
        skin_data = []

        for item in items:
            name = item.get("short_name", "") or item.get("name", "")
            market_hash = item.get("market_hash_name", "")
            price = float(item.get("price", 0) or 0)
            sell_count = item.get("sell_count", 0)
            platform = item.get("platform", "")
            ratio = item.get("ratio", 0)
            rarity = item.get("rarity", "")
            buy_price = float(item.get("buy_price", 0) or 0)

            if not name or price <= 0:
                continue

            total_price += price
            total_volume += sell_count

            # 价格区间
            spread = ""
            if buy_price > 0 and buy_price != price:
                spread = f" | 求购 ¥{buy_price:.0f}"

            summary = f"{platform} ¥{price:.2f}{spread} | {rarity} | 成交量 {sell_count}件 | 比例 {ratio:.1f}%"

            score = min(10, max(2, int(price / 200) + min(sell_count // 100, 5)))

            news_list.append({
                "title": f"{name} ¥{price:.2f}",
                "url": f"https://firepulse.com.cn/#/home",
                "source": "CSGO大盘",
                "score": score,
                "comments": sell_count,
                "summary": summary,
            })

            skin_data.append({
                "name": name,
                "price": price,
                "volume": sell_count,
            })

        # 大盘概览
        if skin_data:
            avg_price = total_price / len(skin_data)
            top3 = " · ".join(f"{s['name'][:12]} ¥{s['price']:.0f}" for s in skin_data[:3])

            index_summary = (
                f"FirePulse大盘均价 ¥{avg_price:.2f} | "
                f"样本 {len(skin_data)} 款 | "
                f"总成交量 {total_volume}件 | "
                f"热门: {top3}"
            )

            index_item = {
                "title": f"🔫 CS:GO FirePulse大盘 ¥{avg_price:.2f}",
                "url": "https://firepulse.com.cn/#/home",
                "source": "CSGO大盘",
                "score": 9,
                "comments": total_volume,
                "summary": index_summary,
            }
            news_list.insert(0, index_item)

    except Exception as e:
        print(f"[CSGO] FirePulse抓取失败: {e}")

    print(f"[CSGO] 抓取完成: {len(news_list)} 条")
    return news_list


if __name__ == "__main__":
    for n in fetch_csgo_market()[:5]:
        print(f"  {n['title'][:60]}")
