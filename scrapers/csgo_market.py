"""
CS:GO 皮肤大盘指数爬虫
数据来源: SteamDT (open.steamdt.com) — 国内最大CS2饰品数据平台
"""

import os
import concurrent.futures
import requests
from config import SOURCES

# 大盘指数标杆皮肤
INDEX_SKINS = [
    "AK-47 | Redline (Field-Tested)",
    "AWP | Asiimov (Field-Tested)",
    "M4A4 | Asiimov (Field-Tested)",
    "AWP | Redline (Field-Tested)",
    "USP-S | Orion (Field-Tested)",
    "P250 | Supernova (Field-Tested)",
    "MAC-10 | Neon Rider (Field-Tested)",
    "Glock-18 | Water Elemental (Field-Tested)",
    "SSG 08 | Blood in the Water (Field-Tested)",
    "Desert Eagle | Hypnotic (Field-Tested)",
    "M4A1-S | Guardian (Field-Tested)",
    "P90 | Asiimov (Field-Tested)",
]

STEAMDT_BASE = "https://open.steamdt.com"


def _load_dotenv():
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = value


_load_dotenv()


def _get_price(market_hash_name):
    """查询单个皮肤在各平台的价格"""
    api_key = os.environ.get("STEAMDT_API_KEY", "")
    if not api_key:
        return None

    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }
        params = {"marketHashName": market_hash_name}
        resp = requests.get(
            f"{STEAMDT_BASE}/open/cs2/v1/price/single",
            params=params,
            headers=headers,
            timeout=15,
        )
        data = resp.json()
        if not data.get("success"):
            return None

        platforms = data.get("data", [])
        if not platforms:
            return None

        # 各平台最低价
        buff_price = None
        c5_price = None
        igxe_price = None
        steam_price = None

        for p in platforms:
            plat = p.get("platform", "")
            price = p.get("sellPrice", 0) or 0
            if plat == "BUFF" and not buff_price:
                buff_price = price
            elif plat == "C5" and not c5_price:
                c5_price = price
            elif plat == "IGXE" and not igxe_price:
                igxe_price = price
            elif plat == "STEAM" and not steam_price:
                steam_price = price

        main_price = buff_price or c5_price or igxe_price or steam_price or 0

        return {
            "name": market_hash_name,
            "buff_price": buff_price,
            "c5_price": c5_price,
            "igxe_price": igxe_price,
            "steam_price": steam_price,
            "main_price": main_price,
        }
    except Exception:
        return None


def fetch_csgo_market():
    """从 SteamDT 抓取 CS:GO 大盘指数"""
    config = SOURCES.get("csgo", {})
    if not config.get("enabled", True):
        return []

    max_items = config.get("max_items", 10)
    news_list = []

    api_key = os.environ.get("STEAMDT_API_KEY", "")
    if not api_key:
        print("[CSGO] 未设置 STEAMDT_API_KEY，跳过")
        return []

    try:
        # 并行查询所有标杆皮肤
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(_get_price, skin): skin
                for skin in INDEX_SKINS[:max_items]
            }
            for f in concurrent.futures.as_completed(futures):
                result = f.result()
                if result:
                    results.append(result)

        if not results:
            raise Exception("所有皮肤查询失败")

        # 按价格排序
        results.sort(key=lambda x: x["main_price"], reverse=True)

        total_price = 0
        skin_data = []

        for item in results:
            name = item["name"]
            short_name = name.split(" (")[0] if " (" in name else name
            price = item["main_price"]
            total_price += price

            # 平台价格字符串
            parts = []
            if item["buff_price"]:
                parts.append(f"Buff ¥{item['buff_price']:.2f}")
            if item["c5_price"]:
                parts.append(f"C5 ¥{item['c5_price']:.0f}")
            if item["igxe_price"]:
                parts.append(f"IGXE ¥{item['igxe_price']:.0f}")
            summary = " | ".join(parts)

            news_list.append({
                "title": f"{short_name} ¥{price:.2f}",
                "url": f"https://buff.163.com/goods?search={name}",
                "source": "CSGO大盘",
                "score": min(10, max(1, int(price / 50))),
                "comments": len(parts),  # 平台数
                "summary": summary,
            })

            skin_data.append({
                "name": short_name,
                "price": price,
            })

        # 大盘指数概览
        if skin_data:
            avg_price = total_price / len(skin_data)
            top3_names = " · ".join(s["name"][:12] for s in skin_data[:3])

            index_summary = (
                f"SteamDT大盘均价 ¥{avg_price:.2f} | "
                f"涵盖 {len(skin_data)} 款标杆皮肤 | "
                f"最贵: {skin_data[0]['name']} ¥{skin_data[0]['price']:.0f} | "
                f"标杆: {top3_names}"
            )

            index_item = {
                "title": f"🔫 CS:GO 大盘均价 ¥{avg_price:.2f}",
                "url": "https://www.steamdt.com",
                "source": "CSGO大盘",
                "score": 9,
                "comments": len(skin_data),
                "summary": index_summary,
            }
            news_list.insert(0, index_item)

    except Exception as e:
        print(f"[CSGO] 抓取失败: {e}")

    print(f"[CSGO] 抓取完成: {len(news_list)} 条")
    return news_list


if __name__ == "__main__":
    for n in fetch_csgo_market()[:5]:
        print(f"  {n['title'][:60]}")
