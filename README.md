# PyInfraGuard

Асинхронный отказоустойчивый демон на Python для высоконагруженного мониторинга API Wildberries. Решение обеспечивает точный контроль лимитов запросов, сбор метрик для Prometheus и мгновенное оповещение об инцидентах через Telegram.

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Code style](https://img.shields.io/badge/code%20style-ruff-black.svg)
![Type checked](https://img.shields.io/badge/mypy-strict-blue.svg)
![Tests](https://img.shields.io/badge/pytest-passing-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

---

## 🛠 Технологический стек
* **Core:** Python 3.11+, `asyncio`, `aiohttp`
* **Limiter:** Реализация алгоритма Token Bucket
* **Monitoring:** Интеграция с `prometheus_client`
* **Alerting:** `aiogram` для уведомлений
* **Quality Control:** `ruff`, `mypy` (strict mode), `pytest`

## 🚀 Основные возможности
- **Rate Limiting:** Интеллектуальный контроль частоты запросов для избежания банов.
- **Observability:** Полная поддержка экспорта метрик для Grafana/Prometheus.
- **Reliability:** Асинхронные контекстные менеджеры и обработка исключений.
- **Alerting:** Мгновенные уведомления в Telegram при критических сбоях или достижении пороговых значений.

## 📦 Установка

1. Клонировать репозиторий:
   ```bash
   git clone [https://github.com/MChuvilevM/PyInfraGuard.git](https://github.com/MChuvilevM/PyInfraGuard.git)
   cd PyInfraGuard

    Установить зависимости:
    Bash

    pip install -r requirements.txt

🧪 Тестирование

Проект полностью покрыт асинхронными тестами. Запуск через pytest:
Bash

pytest

Developed by MChuvilevM
