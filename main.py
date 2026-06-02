#!/usr/bin/env python3
"""
新闻聚合网站 — 主调度脚本
流程: 抓取 → AI筛选 → 生成网站

用法:
    python main.py                    # 正常运行
    python main.py --skip-ai          # 跳过 AI 筛选（测试用）
    python main.py --source hackernews  # 只抓取指定来源
"""

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import argparse
import concurrent.futures
import json
import os
import time
from datetime import datetime

from config import OUTPUT_DIR
from scrapers import (
    fetch_hackernews,
    fetch_reddit,
    fetch_bbc,
    fetch_github_trending,
    fetch_solidot,
    fetch_weibo,
    fetch_xkcd,
    fetch_producthunt,
    fetch_bilibili,
)
from ai_processor import process_news
from generate_site import generate_site

# 所有爬虫函数映射
SCRAPERS = {
    "hackernews": fetch_hackernews,
    "reddit": fetch_reddit,
    "bbc": fetch_bbc,
    "github_trending": fetch_github_trending,
    "solidot": fetch_solidot,
    "weibo": fetch_weibo,
    "xkcd": fetch_xkcd,
    "producthunt": fetch_producthunt,
    "bilibili": fetch_bilibili,
}


def fetch_all(sources=None, parallel=True):
    """并行抓取所有新闻源"""
    if sources is None:
        sources = list(SCRAPERS.keys())

    all_news = []

    if parallel and len(sources) > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(sources)) as executor:
            futures = {executor.submit(SCRAPERS[s]): s for s in sources}
            for future in concurrent.futures.as_completed(futures):
                source_name = futures[future]
                try:
                    result = future.result()
                    all_news.extend(result)
                except Exception as e:
                    print(f"[Main] {source_name} 爬虫异常: {e}")
    else:
        for source_name in sources:
            try:
                result = SCRAPERS[source_name]()
                all_news.extend(result)
            except Exception as e:
                print(f"[Main] {source_name} 爬虫异常: {e}")

    return all_news


def save_debug_data(news_list, stage="raw"):
    """保存中间数据用于调试"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    path = os.path.join(OUTPUT_DIR, f"debug_{stage}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(news_list, f, ensure_ascii=False, indent=2)
    print(f"[Main] 调试数据已保存: {path}")


def main():
    parser = argparse.ArgumentParser(description="每日新闻聚合网站生成器")
    parser.add_argument("--skip-ai", action="store_true", help="跳过 AI 筛选")
    parser.add_argument("--source", type=str, help="只抓取指定来源")
    parser.add_argument("--debug", action="store_true", help="保存调试数据")
    args = parser.parse_args()

    start_time = time.time()
    print("=" * 50)
    print(f"📰 新闻聚合网站 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 1. 抓取新闻
    print("\n[1/3] 抓取新闻...")
    sources = [args.source] if args.source else None
    raw_news = fetch_all(sources=sources)

    if args.debug:
        save_debug_data(raw_news, "raw")

    print(f"[1/3] 共抓取 {len(raw_news)} 条原始新闻")

    if not raw_news:
        print("[Main] ⚠️ 没有抓到任何新闻，退出")
        sys.exit(1)

    # 2. AI 筛选
    if args.skip_ai:
        print("\n[2/3] 跳过 AI 筛选，使用原始数据")
        # 按来源均匀采样，保留来源多样性
        from collections import defaultdict
        by_source = defaultdict(list)
        for n in raw_news:
            by_source[n.get("source", "Unknown")].append(n)
        # 每个来源内按热度排序
        for src in by_source:
            by_source[src].sort(key=lambda x: x.get("score", 0), reverse=True)
        # 轮流从每个来源取，直到凑满 50 条
        processed = []
        source_keys = list(by_source.keys())
        idx = [0] * len(source_keys)
        while len(processed) < 50:
            added = False
            for i, src in enumerate(source_keys):
                if idx[i] < len(by_source[src]):
                    n = by_source[src][idx[i]]
                    idx[i] += 1
                    processed.append({
                        "title": n["title"],
                        "url": n.get("url", ""),
                        "source": n.get("source", ""),
                        "score": min(10, max(1, n.get("score", 0) // 100)) if n.get("score", 0) > 10 else 5,
                        "summary": n.get("summary", n["title"])[:150],
                        "categories": ["其他"],
                        "original_score": n.get("score", 0),
                        "original_comments": n.get("comments", 0),
                    })
                    added = True
                    if len(processed) >= 50:
                        break
            if not added:
                break
    else:
        print("\n[2/3] AI 筛选与总结...")
        processed = process_news(raw_news)

        if args.debug:
            save_debug_data(processed, "processed")

        if not processed:
            print("[Main] ⚠️ AI 处理失败，使用降级方案")
            processed = [{
                "title": n["title"],
                "url": n.get("url", ""),
                "source": n.get("source", ""),
                "score": 5,
                "summary": n["title"],
                "categories": ["其他"],
            } for n in raw_news[:30]]

    # 3. 生成网站
    print("\n[3/3] 生成静态网站...")
    output_path = generate_site(processed)

    elapsed = time.time() - start_time
    print(f"\n{'=' * 50}")
    print(f"✅ 完成! 耗时 {elapsed:.1f} 秒")
    print(f"📂 网站文件: {output_path}")
    print(f"🌐 在浏览器中打开 file:///{output_path} 查看")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()
