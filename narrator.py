
def humanize(decision, ticker: str) -> str:
    p = decision.meta.get("price")
    hz = {"short":"краткосрок","mid":"среднесрок","long":"долгосрок"}.get(decision.meta.get("horizon"), "среднесрок")
    head = f"📊 {ticker} — {hz}. Текущая цена: {p:.2f}.

"
    if decision.stance == "WAIT":
        body = ("Сейчас вход не даёт преимущества. Жду, когда цена откроет более выгодную точку "
                "или подтвердит направление. Без суеты.")
    elif decision.stance == "BUY":
        z = f"{decision.entry[0]:.2f}…{decision.entry[1]:.2f}" if decision.entry else "—"
        body = (f"✅ План: LONG
"
                f"→ Вход: {z}
"
                f"→ Цели: {decision.target1:.2f} / {decision.target2:.2f}
"
                f"→ Защита: {decision.stop:.2f}
"
                f"Работаю спокойно: если сценарий ломается — выхожу и жду новую формацию.")
    elif decision.stance == "SHORT":
        z = f"{decision.entry[0]:.2f}…{decision.entry[1]:.2f}" if decision.entry else "—"
        body = (f"✅ План: SHORT
"
                f"→ Вход: {z}
"
                f"→ Цели: {decision.target1:.2f} / {decision.target2:.2f}
"
                f"→ Защита: {decision.stop:.2f}
"
                f"Без героизма: при отмене сценария закрываю позицию.")
    else:
        body = "Ситуация неоднозначна — наблюдаю."
    tail = "

Я не раскрываю внутренние расчёты — даю вывод как человек."
    return head + body + tail
