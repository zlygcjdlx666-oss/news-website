"""
CS:GO 皮肤大盘行情爬虫
抓取 Steam 官方市场 CS:GO 热门饰品数据
"""

import requests
from config import SOURCES


def fetch_csgo_market():
    """抓取 Steam 市场 CS:GO 热门饰品行情"""
    config = SOURCES.get("csgo", {})
    if not config.get("enabled", True):
        return []

    max_items = config.get("max_items", 15)
    news_list = []

    try:
        # Steam 市场搜索 API — CS:GO 成交量最高物品
        url = "https://steamcommunity.com/market/search/render/"
        params = {
            "appid": 730,
            "norender": 1,
            "count": max_items + 5,
            "sort_column": "volume",
            "sort_dir": "desc",
            "currency": 23,  # CNY
        }
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "application/json",
        }

        resp = requests.get(url, params=params, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        items = data.get("results", [])[:max_items]

        if not items:
            raise Exception("Steam 返回空数据")

        total_sell_price = 0
        total_volume = 0
        skin_list = []

        for item in items:
            name = item.get("name", "").strip()
            if not name:
                continue

            # Steam 返回的价格文本: "¥ 123.45"
            price_text = item.get("sell_price_text", "0")
            sell_price = 0
            try:
                sell_price = float(
                    price_text.replace("¥", "").replace(",", "").replace(" ", "").strip()
                )
            except (ValueError, AttributeError):
                pass

            volume = item.get("sell_listings", 0)
            total_sell_price += sell_price
            total_volume += volume

            # 物品类型
            item_type = ""
            type_tags = []
            for tag in item.get("tags", []):
                tag_name = tag.get("localized_tag_name", "")
                if tag_name:
                    type_tags.append(tag_name)
            if type_tags:
                item_type = " | ".join(type_tags[:2])

            summary_parts = [f"售价 ¥{sell_price:.2f}"]
            if item_type:
                summary_parts.append(item_type)
            if volume:
                summary_parts.append(f"挂单 {volume}件")
            summary = " | ".join(summary_parts)

            # 热度评分: 价格越高 + 成交量越多 = 越热门
            score = min(10, max(1, int(sell_price / 100) + min(volume // 200, 5)))

            skin_list.append({
                "name": name,
                "price": sell_price,
                "volume": volume,
            })

            news_list.append({
                "title": f"{name}",
                "url": f"https://steamcommunity.com/market/listings/730/{name.replace(' ', '%20')}",
                "source": "CSGO大盘",
                "score": score,
                "comments": volume,
                "summary": summary,
            })

        # 大盘行情概览
        if skin_list:
            avg_price = total_sell_price / len(skin_list) if skin_list else 0
            top5 = skin_list[:5]
            top5_names = " · ".join(s["name"][:15] for s in top5[:3])

            index_summary = (
                f"Steam市场成交量Top{len(skin_list)}均价 ¥{avg_price:.2f} | "
                f"总挂单量 {total_volume}件 | "
                f"热门: {top5_names}"
            )

            index_item = {
                "title": f"🔫 CS:GO Steam大盘 均价¥{avg_price:.2f}",
                "url": "https://steamcommunity.com/market/search?appid=730",
                "source": "CSGO大盘",
                "score": 8,
                "comments": total_volume,
                "summary": index_summary,
            }
            news_list.insert(0, index_item)

    except Exception as e:
        print(f"[CSGO] Steam市场抓取失败: {e}")

        # 备用：从 Skinport API 获取
        try:
            sp_url = "https://api.skinport.com/v1/items"
            params = {"app_id": 730, "currency": "CNY"}
            resp = requests.get(sp_url, params=params, timeout=15)
            items = resp.json()[:max_items]

            for item in items:
                name = item.get("market_hash_name", "")
                price = item.get("suggested_price", 0) or 0
                news_list.append({
                    "title": name,
                    "url": f"https://skinport.com/item/{item.get('url', '')}",
                    "source": "CSGO大盘",
                    "score": 5,
                    "comments": 0,
                    "summary": f"Skinport参考价 ¥{price:.2f}",
                })
            print(f"[CSGO] Skinport备用源: {len(news_list)} 条")
        except Exception as e2:
            print(f"[CSGO] 备用源也失败: {e2}")

    print(f"[CSGO] 抓取完成: {len(news_list)} 条")
    return news_list


if __name__ == "__main__":
    for n in fetch_csgo_market()[:5]:
        print(f"  {n['title'][:60]} | {n['summary'][:60]}")
