from utils.safe_send import safe_answer
import os
import shutil
from aiogram import Router
from aiogram.types import Message, FSInputFile
from database.db import session
from database.models import User

router = Router()

# Путь к основной базе данных
DB_PATH = "db_data/bot.db"
# Путь к резервной копии базы данных
BACKUP_PATH = "db_data/bot_backup.db"

@router.message(lambda m: m.text and m.text.split()[0].split("@")[0] == "/backup_db")
async def backup_db(message: Message):
    # Получаем пользователя по его Telegram ID
    user = session.query(User).filter_by(game_id=message.from_user.id).first()

    # Проверяем, существует ли пользователь и является ли он администратором
    if not user or not user.is_admin:
        print(f"[DEBUG] Пользователь {message.from_user.id} не админ или не найден")
        await safe_answer(message, "❌ У вас нет доступа.")
        return

    # Проверяем существование основного файла базы данных
    if not os.path.exists(DB_PATH):
        await safe_answer(message, f"❌ Основной файл базы не найден по пути: {DB_PATH}")
        return

    try:
        # Копируем основную базу в резервную копию
        shutil.copy2(DB_PATH, BACKUP_PATH)

        # Вычисляем размер резервной копии в мегабайтах
        file_size = os.path.getsize(BACKUP_PATH) / (1024 * 1024)

        # Сообщаем пользователю о создании бэкапа
        await safe_answer(message, f"✅ Бэкап базы создан: {BACKUP_PATH}\nРазмер: {file_size:.2f} МБ")

        # Если файл больше 50 МБ — сообщаем, что его нельзя отправить через Telegram
        if file_size > 50:
            await safe_answer(message, "⚠️ Бэкап слишком большой для отправки в Telegram (>50 МБ). "
                                       "Скачайте его напрямую с сервера.")
            return

        # Создаём объект файла для отправки
        backup_file = FSInputFile(BACKUP_PATH)
        # Отправляем файл пользователю
        await message.answer_document(document=backup_file, caption="📁 Резервная копия базы данных")

    except Exception as e:
        # Обрабатываем ошибки при копировании или отправке файла
        await safe_answer(message, f"❌ Ошибка при создании/отправке бэкапа: {e}")
