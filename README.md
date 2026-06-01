# 🛡️ PyInfraGuard

Асинхронный отказоустойчивый демон на Python для высоконагруженного мониторинга API Wildberries.

![Python](https://img.shields.io/badge/python-3.11-blue.svg?style=flat-square)
![Code style](https://img.shields.io/badge/code%20style-ruff-black.svg?style=flat-square)
![Type checked](https://img.shields.io/badge/mypy-strict-blue.svg?style=flat-square)
![Tests](https://img.shields.io/badge/pytest-passing-brightgreen.svg?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)

---

## 🏗️ Архитектура проекта

Проект спроектирован как модульное приложение с разделением ответственности:

* **`core/`** — асинхронный клиент для взаимодействия с API.
* **`limiter/`** — реализация алгоритма Token Bucket для контроля лимитов.
* **`alerts/`** — модуль мгновенных уведомлений (Telegram).
* **`metrics/`** — экспортер метрик для Prometheus.

## 🚀 Основные возможности

- **Smart Rate Limiting:** Защита от блокировок API через адаптивный контроль частоты запросов.
- **Observability:** Полная поддержка Prometheus для мониторинга в реальном времени.
- **Reliability:** Обработка ошибок с автоматическим переподключением и асинхронными контекстными менеджерами.
- **Instant Alerting:** Моментальная реакция на сбои через Telegram-бота.

## ⚙️ Установка

1. **Клонирование:**
   ```bash
   git clone [https://github.com/MChuvilevM/PyInfraGuard.git](https://github.com/MChuvilevM/PyInfraGuard.git)
   cd PyInfraGuard

    Установка зависимостей:
    Bash

    pip install -r requirements.txt

🧪 Тестирование

Проект покрыт асинхронными тестами с использованием unittest.mock. Запуск:
Bash

pytest

Developed by MChuvilevM | 2026
