
# ⚛ Republic Bot

Телеграм-бот для управления участниками фракции **Республика** в игре *Wasteland Wars*.  
Бот предоставляет:
- 👤 Профили игроков
- 📚 Навигацию по гайдам
- 📍 Информацию о локациях
- ⚔ Участие в рейдах с напоминаниями
- 📊 Отчёты, журнал пинов
- 🛡 Админ-функции: управление пользователями, гайдами, локациями, рейдами
- 💾 Резервное копирование базы данных

---

## 📂 Структура проекта

```
.
├── main.py                  # Точка входа
├── config.py                 # Конфигурация
├── database/                 # Модели БД
├── handlers/                 # Обработчики команд
├── keyboards/                # Клавиатуры
├── services/                 # Бизнес-логика
├── states/                   # FSM состояния
├── utils/                    # Утилиты
├── db_data/                  # Файлы базы
├── requirements.txt          # Зависимости
├── Dockerfile
├── docker-compose.yml
└── .env
```

---

## 🔑 Пример .env

```env
BOT_TOKEN='ваш_токен_бота'
ADMIN_IDS=[123456789,987654321]
```

---

## 💻 Установка и запуск

### ✅ Windows (PowerShell)

1️⃣ Перейдите в папку проекта:
```powershell
cd C:\Users\Zver\PycharmProjects\Republic_bot
```

2️⃣ Создайте venv:
```powershell
C:\Users\Zver\AppData\Local\Programs\Python\Python313\python.exe -m venv venv
```

3️⃣ Активируйте:
```powershell
.\venv\Scripts\Activate.ps1
```
Если заблокировано — выполните в админ PowerShell:
```powershell
Set-ExecutionPolicy RemoteSigned
```
И снова активируйте.

4️⃣ Установите зависимости:
```powershell
pip install -r requirements.txt
```

5️⃣ Запустите бота:
```powershell
python main.py
```

---

### ✅ Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

---

### ✅ Docker

```bash
docker build -t republic-bot .
docker run -d --name republic_bot_container --env-file .env -v $(pwd)/db_data:/app/db_data republic-bot
```
Или:
```bash
docker-compose up -d
```

---

### ✅ systemd (Linux автозапуск)

Создайте юнит:
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
Активируйте:
```bash
sudo systemctl daemon-reload
sudo systemctl enable republic-bot
sudo systemctl start republic-bot
```

---

### ✅ PyCharm

`Settings → Project: Republic_bot → Python Interpreter`  
→ ⚙ → Add → Existing environment  
→ Укажите путь:
```
C:\Users\Zver\PycharmProjects\Republic_bot\venv\Scripts\python.exe
```

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

---

## 🎯 Готово!

Бот готов к работе.  
Для вопросов и поддержки: обращайтесь к разработчику проекта.
