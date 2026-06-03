"""
网易云音乐热歌榜爬虫
抓取网易云音乐热歌榜 Top 歌曲
"""

import requests
from config import SOURCES


def fetch_music():
    """抓取网易云音乐热歌榜"""
    config = SOURCES["music"]
    if not config["enabled"]:
        return []

    max_items = config["max_items"]
    news_list = []

    try:
        # 网易云热歌榜 API (无需登录)
        url = "https://music.163.com/api/playlist/detail"
        params = {"id": 3778678}  # 热歌榜 playlist ID
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://music.163.com/",
        }
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        tracks = data.get("result", {}).get("tracks", [])[:max_items]

        for i, track in enumerate(tracks):
            title = track.get("name", "").strip()
            artists = ", ".join(ar.get("name", "") for ar in track.get("artists", []))
            album = track.get("album", {}).get("name", "")
            song_id = track.get("id", "")

            parts = [f"歌手: {artists}"]
            if album:
                parts.append(f"专辑: {album}")
            parts.append(f"排名: #{i+1}")
            summary = " | ".join(parts)

            # 得分：排名越高分越高
            score = max(1, 10 - i // 3)

            news_list.append({
                "title": f"{title} — {artists}",
                "url": f"https://music.163.com/song?id={song_id}" if song_id else "",
                "source": "网易云音乐",
                "score": score,
                "comments": 0,
                "summary": summary,
            })

    except Exception as e:
        print(f"[Music] 抓取失败: {e}")

    print(f"[Music] 抓取完成: {len(news_list)} 条")
    return news_list


if __name__ == "__main__":
    for n in fetch_music()[:5]:
        print(f"  {n['title'][:60]}... | {n['summary'][:60]}")
