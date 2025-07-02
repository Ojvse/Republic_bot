
# ⚛ Republic Bot

Телеграм-бот для управления участниками фракции **Республика** в игре *Wasteland Wars* (или аналогичной).  
Основные возможности:
- 👤 Профили игроков
- 📚 Гайды с древовидной навигацией
- 📍 Информация о локациях
- ⚔ Рейды (участие, напоминания, отчёты)
- 🛡 Админ-панель (пользователи, гайды, локации, рейды)
- 📊 Журнал пинов и отчётов
- 💾 Резервные копии базы

---

## 🇬🇧 Setup and launch

### ✅ Windows — виртуальное окружение

Перейдите в проект:
```powershell
cd C:\Users\Zver\PycharmProjects\Republic_bot
```

Создайте venv:
```powershell
C:\Users\Zver\AppData\Local\Programs\Python\Python313\python.exe -m venv venv
```

Активируйте:
```powershell
.\venv\Scripts\Activate.ps1
```

Если заблокировано — запустите PowerShell от имени администратора:
```powershell
Set-ExecutionPolicy RemoteSigned
```
И снова активируйте:
```powershell
.\venv\Scripts\Activate.ps1
```

Установите зависимости:
```powershell
pip install -r requirements.txt
```

Запустите бота:
```powershell
python main.py
```

---

### ✅ Linux / macOS

Создайте окружение:
```bash
python3 -m venv venv
source venv/bin/activate
```

Установите зависимости:
```bash
pip install -r requirements.txt
```

Запустите бота:
```bash
python main.py
```

---

### ✅ Docker

Создайте образ:
```bash
docker build -t republic-bot .
```

Запустите:
```bash
docker run -d --name republic_bot_container --env-file .env -v $(pwd)/db_data:/app/db_data republic-bot
```

Или через docker-compose:
```bash
docker-compose up -d
```

---

### ✅ systemd (Linux автозапуск)

Создайте файл:
```bash
sudo nano /etc/systemd/system/republic-bot.service
```

Пример содержимого:
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

Статус:
```bash
sudo systemctl status republic-bot
```

---

## ✅ Через PyCharm

`Settings → Project: Republic_bot → Python Interpreter` → ⚙ → Add → Existing environment → укажите:
```
C:\Users\Zver\PycharmProjects\Republic_bot\venv\Scripts\python.exe
```

PyCharm настроит venv автоматически.

---

## 🎯 Готово!
Теперь бот готов к работе в выбранной среде.
