"""
CS:GO 皮肤大盘指数 — 抓取自 firepulse.com.cn
FirePulse 是百万 CS2 玩家使用的饰品行情平台
"""

import requests
from config import SOURCES

FIREPULSE_API = "https://api.firepulse.com.cn/v1/market/facade/category/large_cap"


def fetch_csgo_market():
    """从 FirePulse 抓取 CS:GO 大盘指数"""
    config = SOURCES.get("csgo", {})
    if not config.get("enabled", True):
        return []

    news_list = []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Referer": "https://firepulse.com.cn/",
        }
        resp = requests.post(FIREPULSE_API, json={}, headers=headers, timeout=15)
        data = resp.json()

        if data.get("code") != 200:
            raise Exception(f"API错误: {data.get('message', 'unknown')}")

        result = data.get("data", {})

        # 大盘指数基本信息
        index_info = result.get("index_basic_info", {})
        current_index = index_info.get("current_index", 0)
        change_index = index_info.get("change_index", 0)
        change_percent = index_info.get("change_index_percent", 0)
        max_index = index_info.get("max_index", 0)
        min_index = index_info.get("min_index", 0)
        change_day = index_info.get("change_day", 0)
        latest_time = index_info.get("latest_time", "")

        # 交易数据
        trade_info = result.get("trade_basic_info", {})
        today_amount = trade_info.get("today_amount", 0) / 10000  # 转万元
        today_volume = trade_info.get("today_volume", 0)
        mom_amount = trade_info.get("mom_trade_amount", 0)

        # 涨跌统计
        updown = result.get("updown_basic_info", {})
        up_count = updown.get("up_count", 0)
        flat_count = updown.get("flat_count", 0)
        down_count = updown.get("down_count", 0)

        # 涨跌方向
        direction = "📈" if change_index > 0 else "📉" if change_index < 0 else "➡"
        change_sign = "+" if change_index >= 0 else ""

        # 大盘指数概览
        index_title = f"🔫 CS:GO 大盘指数 {current_index} {direction}{change_sign}{change_index}({change_sign}{change_percent}%)"
        index_summary = (
            f"今日 {current_index} | "
            f"{direction} {change_sign}{change_index} ({change_sign}{change_percent}%) | "
            f"最高 {max_index} 最低 {min_index} | "
            f"连涨 {change_day} 天 | "
            f"成交额 ¥{today_amount:.0f}万 | "
            f"成交量 {today_volume}件 | "
            f"涨 {up_count} / 平 {flat_count} / 跌 {down_count}"
        )

        index_item = {
            "title": index_title,
            "url": "https://firepulse.com.cn/#/home",
            "source": "CSGO大盘",
            "score": min(10, max(6, int(abs(change_percent) + 5))),
            "comments": today_volume,
            "summary": index_summary,
        }
        news_list.append(index_item)

        # 涨跌分布
        total = up_count + flat_count + down_count
        if total > 0:
            up_pct = up_count * 100 / total
            down_pct = down_count * 100 / total
            dist_summary = (
                f"📊 涨跌分布: 📈{up_count}({up_pct:.0f}%) "
                f"➡{flat_count}({flat_count*100/total:.0f}%) "
                f"📉{down_count}({down_pct:.0f}%)"
            )
            news_list.append({
                "title": f"📊 涨跌分布 {latest_time}",
                "url": "https://firepulse.com.cn/#/home",
                "source": "CSGO大盘",
                "score": 6,
                "comments": total,
                "summary": dist_summary,
            })

        # 交易量
        news_list.append({
            "title": f"💹 今日成交额 ¥{today_amount:.0f}万",
            "url": "https://firepulse.com.cn/#/home",
            "source": "CSGO大盘",
            "score": 5,
            "comments": today_volume,
            "summary": f"成交额 ¥{today_amount:.0f}万 | 成交量 {today_volume}件 | 环比 {mom_amount:.1f}%",
        })

    except Exception as e:
        print(f"[CSGO] FirePulse抓取失败: {e}")

    print(f"[CSGO] 抓取完成: {len(news_list)} 条")
    return news_list


if __name__ == "__main__":
    for n in fetch_csgo_market():
        print(f"  {n['title'][:80]}")
