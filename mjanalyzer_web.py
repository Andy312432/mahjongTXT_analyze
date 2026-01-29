#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Browser automation for https://mjanalyzer.netlify.app/

Examples:
  python mjanalyzer_web.py --hand "123m456p789s123z11m"
  python mjanalyzer_web.py --hand "1m 1m 2m 3m 4p 5p 6p 7s 8s 9s 1z 2z 3z"
  python mjanalyzer_web.py --hand "123m456p789s123z11m" --dead "1m1m9s"
  python mjanalyzer_web.py --hand "123m456p789s123z11m" --headless --screenshot result.png
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from typing import Dict, List

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover - runtime dependency
    sync_playwright = None


URL_DEFAULT = "https://mjanalyzer.netlify.app/"

SUITS = ["m", "p", "s", "z"]
ID_TO_INDEX: Dict[str, int] = {}
_idx = 0
for _suit in SUITS:
    _max_rank = 7 if _suit == "z" else 9
    for _rank in range(1, _max_rank + 1):
        _tile_id = f"{_rank}{_suit}"
        ID_TO_INDEX[_tile_id] = _idx
        _idx += 1


def _validate_tile_id(tile_id: str) -> None:
    if len(tile_id) != 2:
        raise ValueError(f"Invalid tile id: {tile_id}")
    num, suit = tile_id[0], tile_id[1]
    if suit not in SUITS:
        raise ValueError(f"Invalid tile suit: {tile_id}")
    if not num.isdigit():
        raise ValueError(f"Invalid tile number: {tile_id}")
    n = int(num)
    if suit == "z":
        if n < 1 or n > 7:
            raise ValueError(f"Honor tile out of range: {tile_id}")
    else:
        if n < 1 or n > 9:
            raise ValueError(f"Suit tile out of range: {tile_id}")


def _parse_compact_token(token: str) -> List[str]:
    token = token.strip().lower()
    if not token:
        return []
    matches = list(re.finditer(r"(\d+)([mpsz])", token))
    if not matches:
        raise ValueError(f"Invalid tile string: {token}")
    joined = "".join(m.group(0) for m in matches)
    if joined != token:
        raise ValueError(f"Invalid tile string: {token}")
    tiles: List[str] = []
    for m in matches:
        digits, suit = m.group(1), m.group(2)
        for ch in digits:
            tile_id = f"{ch}{suit}"
            _validate_tile_id(tile_id)
            tiles.append(tile_id)
    return tiles


def parse_tiles(text: str) -> List[str]:
    if not text:
        return []
    s = text.strip()
    if not s:
        return []
    s = re.sub(r"[,\|;/]+", " ", s)
    tokens = s.split()
    tiles: List[str] = []
    if len(tokens) > 1:
        for tok in tokens:
            tiles.extend(_parse_compact_token(tok))
    else:
        tiles.extend(_parse_compact_token(s))
    return tiles

LABELS: Dict[str, str] = {
    "1m": "一萬",
    "2m": "二萬",
    "3m": "三萬",
    "4m": "四萬",
    "5m": "五萬",
    "6m": "六萬",
    "7m": "七萬",
    "8m": "八萬",
    "9m": "九萬",
    "1p": "一餅",
    "2p": "二餅",
    "3p": "三餅",
    "4p": "四餅",
    "5p": "五餅",
    "6p": "六餅",
    "7p": "七餅",
    "8p": "八餅",
    "9p": "九餅",
    "1s": "一索",
    "2s": "二索",
    "3s": "三索",
    "4s": "四索",
    "5s": "五索",
    "6s": "六索",
    "7s": "七索",
    "8s": "八索",
    "9s": "九索",
    "1z": "東",
    "2z": "南",
    "3z": "西",
    "4z": "北",
    "5z": "白",
    "6z": "發",
    "7z": "中",
}


def _validate_counts(hand: List[str], dead: List[str]) -> None:
    if not hand:
        raise ValueError("手牌不可為空")
    if len(hand) % 3 == 0:
        raise ValueError("牌張數不可為 3 的倍數 (例如 3, 6, 9, 12, 15)")
    if len(hand) > 17:
        raise ValueError("手牌張數不可超過 17")
    hc = Counter(hand)
    dc = Counter(dead)
    for tile_id in hc:
        if tile_id not in ID_TO_INDEX:
            raise ValueError(f"未知牌: {tile_id}")
        if hc[tile_id] > 4:
            raise ValueError(f"手牌 {tile_id} 超過 4 張")
    for tile_id in dc:
        if tile_id not in ID_TO_INDEX:
            raise ValueError(f"未知牌: {tile_id}")
        if dc[tile_id] > 4:
            raise ValueError(f"已現出牌 {tile_id} 超過 4 張")
    for tile_id in set(hc) | set(dc):
        if hc[tile_id] + dc[tile_id] > 4:
            raise ValueError(f"{tile_id} 手牌+已現出超過 4 張")


def _open_panel(page) -> None:
    # Prefer the helper hint text; fall back to the empty-hand prompt.
    try:
        page.get_by_text("點擊上方綠色區域即可開啟選牌面板。").click(timeout=1500)
        return
    except Exception:
        pass
    try:
        page.get_by_text("點擊此處選擇手牌...").click(timeout=1500)
        return
    except Exception:
        pass
    # Last resort: click the green hand area.
    page.locator("section").filter(has_text="手牌").first.click()


def _get_panel(page):
    hand_tab = page.get_by_role("button", name=re.compile(r"^手牌$"))
    dead_tab = page.get_by_role("button", name=re.compile(r"^海底$"))
    panel = page.locator("div").filter(has=hand_tab).filter(has=dead_tab).first
    panel.wait_for(state="visible", timeout=5000)
    return panel


def _select_mode(panel, mode: str) -> None:
    if mode == "hand":
        panel.get_by_role("button", name=re.compile(r"^手牌$")).click()
        panel.get_by_text("點擊下方牌加入手牌").wait_for(timeout=3000)
    elif mode == "dead":
        panel.get_by_role("button", name=re.compile(r"^海底$")).click()
        panel.get_by_text("點擊下方牌標記為已現出").wait_for(timeout=3000)
    else:
        raise ValueError("mode must be hand or dead")


def _click_tile(panel, tile_id: str) -> None:
    label = LABELS.get(tile_id)
    if not label:
        raise ValueError(f"未知牌: {tile_id}")
    # The panel container also includes the main hand area; scope to the tile grid.
    grid = panel.locator("div.space-y-4").first
    grid.locator(f'button[title="{label}"]').first.click()


def _close_panel(panel) -> None:
    # Close button is the only icon-only button in the panel header.
    btn = panel.locator("button").filter(has=panel.locator("svg")).first
    try:
        btn.click(timeout=1500)
    except Exception:
        # If close fails, continue; analysis button is still clickable.
        pass


def run_automation(
    hand: List[str],
    dead: List[str],
    url: str,
    headless: bool,
    slow_mo: int,
    timeout_ms: int,
    screenshot: str | None,
    pause: bool,
) -> int:
    if sync_playwright is None:
        print(
            "Playwright 未安裝。請先執行:\n  pip install playwright\n  playwright install",
            file=sys.stderr,
        )
        return 2

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=slow_mo)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(timeout_ms)

        page.goto(url, wait_until="networkidle")
        page.get_by_text("麻將手牌分析").wait_for(timeout=10000)

        _open_panel(page)
        panel = _get_panel(page)

        # Clear any existing selections.
        try:
            panel.get_by_role("button", name=re.compile(r"^清除$")).click(timeout=1500)
        except Exception:
            pass

        _select_mode(panel, "hand")
        for t in hand:
            _click_tile(panel, t)

        if dead:
            _select_mode(panel, "dead")
            for t in dead:
                _click_tile(panel, t)

        _close_panel(panel)

        page.get_by_role("button", name=re.compile(r"^分析牌型$")).click()
        page.get_by_text("分析結果").wait_for(timeout=15000)

        if screenshot:
            page.screenshot(path=screenshot, full_page=True)

        if pause and not headless:
            input("已完成分析，按 Enter 關閉瀏覽器...")

        browser.close()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Automate mjanalyzer.netlify.app with Playwright."
    )
    parser.add_argument(
        "--hand",
        "-H",
        required=True,
        help="Hand tiles, e.g. 123m456p789s123z11m or '1m 2m 3m ...'.",
    )
    parser.add_argument(
        "--dead",
        "-D",
        default="",
        help="Dead/seen tiles, same format as --hand.",
    )
    parser.add_argument(
        "--url",
        default=URL_DEFAULT,
        help="Site URL (default: https://mjanalyzer.netlify.app/).",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode.",
    )
    parser.add_argument(
        "--slowmo",
        type=int,
        default=150,
        help="Slow motion delay per action in ms (default: 150).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=15000,
        help="Action timeout in ms (default: 15000).",
    )
    parser.add_argument(
        "--screenshot",
        default="",
        help="Save a screenshot after analysis (path).",
    )
    parser.add_argument(
        "--no-pause",
        action="store_true",
        help="Do not wait for Enter before closing the browser.",
    )
    args = parser.parse_args()

    try:
        hand = parse_tiles(args.hand)
        dead = parse_tiles(args.dead)
        _validate_counts(hand, dead)
    except ValueError as exc:
        print(f"輸入錯誤: {exc}", file=sys.stderr)
        return 2

    screenshot = args.screenshot or None
    try:
        return run_automation(
            hand=hand,
            dead=dead,
            url=args.url,
            headless=args.headless,
            slow_mo=args.slowmo,
            timeout_ms=args.timeout,
            screenshot=screenshot,
            pause=not args.no_pause,
        )
    except PlaywrightTimeoutError as exc:
        print(f"操作逾時: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
