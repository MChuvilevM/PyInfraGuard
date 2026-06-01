# 🛡️ PyInfraGuard

Асинхронный отказоустойчивый демон на Python для высоконагруженного мониторинга API Wildberries.

![Python](https://img.shields.io/badge/python-3.11-blue.svg?style=flat-square)
![Code style](https://img.shields.io/badge/code%20style-ruff-black.svg?style=flat-square)
![Type checked](https://img.shields.io/badge/mypy-strict-blue.svg?style=flat-square)
![Tests](https://img.shields.io/badge/pytest-passing-brightgreen.svg?style=flat-square)

---

## 🏗️ Архитектура
* **core/** — асинхронный клиент API.
* **limiter/** — алгоритм Token Bucket.
* **alerts/** — Telegram-уведомления.
* **metrics/** — Prometheus-метрики.

## 🚀 Возможности
- **Smart Rate Limiting:** Защита от банов API.
- **Observability:** Prometheus-метрики в реальном времени.
- **Reliability:** Асинхронные контекстные менеджеры.
- **Alerting:** Мгновенные уведомления в Telegram.

---

## ⚙️ Установка
```bash
git clone [https://github.com/MChuvilevM/PyInfraGuard.git](https://github.com/MChuvilevM/PyInfraGuard.git)
cd PyInfraGuard
pip install -r requirements.txt
```
## 🧪 Тестирование
```bash
pytest
```
Developed by MChuvilevM | 2026
