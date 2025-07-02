
# ⚛ Republic Bot

Телеграм-бот для управления участниками фракции "Республика" в игре **Wasteland Wars** (или аналогичной). Бот предоставляет функционал для игроков и администраторов: профили, рейды, гайды, локации, рассылки и отчёты.

---

## 🚀 Возможности

### Для пользователей:
- 👤 Просмотр и обновление собственного профиля
- 📚 Навигация по гайдам с древовидной структурой
- 📍 Просмотр информации о локациях
- ⚔ Участие в рейдах с кнопками "Я иду", "Я не иду", "Напомнить"
- 🔔 Автоматические напоминания перед рейдами

### Для администраторов:
- 🛡 Управление пользователями (добавление, редактирование, удаление)
- 📅 Управление рейдами (создание, удаление, отчёты, выдача пинов)
- 📒 Журнал отправленных пинов
- 📢 Массовые рассылки по бандaм или всем участникам
- 📘 Управление структурой гайдов
- 📍 Управление локациями
- 📊 Построение отчётов по участию
- 💾 Создание резервных копий БД

---

## ⚙️ Стек технологий

- **Python 3.11+**
- **Aiogram 3**
- **SQLAlchemy + SQLite**
- **APScheduler**
- **Docker (поддерживается)**

---

## 📂 Структура проекта

```
.
├── main.py
├── config.py
├── database/
├── handlers/
├── keyboards/
├── services/
├── states/
├── utils/
├── db_data/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env
```

---

## 🔑 Настройка переменных окружения

В файле **.env**:
```
BOT_TOKEN=ваш_токен_бота
ADMIN_IDS=[список_числовых_ID]
```
Пример:
```
BOT_TOKEN='7624196025:AAFy.......K6J4_H1H6E'
ADMIN_IDS=[123456789,987654321,111222333]
```

---

## 💻 Запуск

### Локально

1️⃣ Установите Python 3.11+

2️⃣ Установите зависимости:
```bash
pip install -r requirements.txt
```

3️⃣ Запустите бота:
```bash
python main.py
```

---

### Docker

Бот готов для запуска в Docker с помощью предоставленных файлов:

#### Построение образа
```bash
docker build -t republic-bot .
```

#### Запуск контейнера
```bash
docker run -d --name republic_bot_container --env-file .env -v $(pwd)/db_data:/app/db_data republic-bot
```

#### Альтернативно с docker-compose
```bash
docker-compose up -d
```

Файл `docker-compose.yml` уже настроен для использования `.env` и сохранения данных БД.

---

## 🌐 Размещение на сервере

- Для systemd создайте unit-файл, например:
  ```ini
  [Unit]
  Description=Republic Bot
  After=network.target

  [Service]
  WorkingDirectory=/path/to/bot
  ExecStart=/path/to/bot/venv/bin/python main.py
  Restart=always
  EnvironmentFile=/path/to/bot/.env

  [Install]
  WantedBy=multi-user.target
  ```

- Для Docker используйте автозапуск контейнера или docker-compose с параметром `restart: always`.

---

## 📦 Зависимости

```
aiogram==3.20.0
aiohttp==3.11.6
aiosqlite==0.21.0
python-dotenv==1.0.1
APScheduler==3.11.0
pytz==2025.1
tzdata==2025.1
SQLAlchemy==2.0.38
pydantic==2.10.6
regex==2024.11.6
```
