import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from handlers import register_handlers

from database.models import Base
from database.db import engine

from utils.scheduler import raid_reminder_loop


# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
)


async def main():
    # Создание таблиц БД, если их ещё нет
    Base.metadata.create_all(bind=engine)
    print("[INIT] Таблицы базы данных созданы")

    # Инициализация бота
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # Инициализация диспетчера с хранилищем состояний
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация обработчиков
    register_handlers(dp)
    print("[INIT] Хендлеры зарегистрированы")

    # Запуск фоновой задачи напоминаний
    asyncio.create_task(raid_reminder_loop(bot))

    # Удаление вебхука перед запуском пулинга
    await bot.delete_webhook(drop_pending_updates=True)

    # Запуск пулинга с явным указанием обрабатываемых типов событий
    await dp.start_polling(
        bot,
        allowed_updates=["message", "callback_query", "chat_member"],
    )


# Точка входа
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен")
