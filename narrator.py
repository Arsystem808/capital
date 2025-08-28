# -*- coding: utf-8 -*-
"""
Форматирование ответа для пользователя.
Принимает словарь/объект с полями: stance, entry, target1, target2, stop, meta.
Ничего «технического» (пивоты и т.п.) наружу не отдаём.
"""

from typing import Any, Optional, Tuple

def _fmt_price(x: Optional[float]) -> str:
    return "—" if x is None else f"{x:,.2f}"

def _fmt_range(r: Optional[Tuple[float, float]]) -> str:
    if not r or len(r) != 2 or r[0] is None or r[1] is None:
        return "—"
    a, b = r
    if a > b:
        a, b = b, a
    return f"{a:,.2f}…{b:,.2f}"

def humanize(decision: Any) -> str:
    """
    Пример ожидаемой структуры:
    decision = {
        "stance": "BUY" | "SHORT" | "WAIT",
        "entry": (low, high) | None,
        "target1": float | None,
        "target2": float | None,
        "stop": float | None,
        "meta": {"ticker": "QQQ", "price": 571.97, "horizon": "mid", "notes": "..."}
    }
    """
    d = decision
    stance = str(d.get("stance", "WAIT")).upper()
    entry = d.get("entry")
    t1 = d.get("target1")
    t2 = d.get("target2")
    st = d.get("stop")
    meta = d.get("meta") or {}

    ticker = meta.get("ticker", "").upper() or "—"
    price  = meta.get("price")
    hz     = meta.get("horizon", "")
    notes  = meta.get("notes")

    hz_label = {"short":"Трейд (1–5 дней)", "mid":"Среднесрок (1–4 недели)", "long":"Долгосрок (1–6 месяцев)"}.get(hz, "")

    head = f"📊 {ticker} — текущая цена: {_fmt_price(price)}"
    if hz_label:
        head += f"\n🕒 Горизонт: {hz_label}"

    if stance == "WAIT":
        body = "🟡 Сейчас лучше подождать — приоритет не на нашей стороне. Ищем более качественную точку входа."
        alt  = None
    elif stance == "BUY":
        body = (
            f"🟢 Базовый план: BUY\n"
            f"• Вход: {_fmt_range(entry)}\n"
            f"• Цели: {_fmt_price(t1)} / {_fmt_price(t2)}\n"
            f"• Защита (стоп): {_fmt_price(st)}"
        )
        alt = "Если сценарий ломается — быстро выходим и ждём новую формацию."
    elif stance == "SHORT":
        body = (
            f"🔴 Базовый план: SHORT\n"
            f"• Вход: {_fmt_range(entry)}\n"
            f"• Цели: {_fmt_price(t1)} / {_fmt_price(t2)}\n"
            f"• Защита (стоп): {_fmt_price(st)}"
        )
        alt = "Если импульс не подтверждается — не тащим позицию силой, ждём новое преимущество."
    else:
        body = "🟡 Сейчас лучше подождать."
        alt  = None

    tail_lines = []
    if notes:
        tail_lines.append(f"💬 Замечание: {notes}")
    if alt:
        tail_lines.append(f"⚠️ {alt}")

    msg = head + "\n\n" + body
    if tail_lines:
        msg += "\n\n" + "\n".join(tail_lines)
    return msg
