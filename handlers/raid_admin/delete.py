from utils.safe_send import safe_answer, safe_send_message
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.db import session
from database.models import RaidEvent
from states.raid_states import DeleteRaid
from keyboards.cancel import cancel_keyboard
from services.navigation import return_to_raid_admin_menu

router = Router()


@router.message(F.text == "🗑 Удалить рейд")
async def delete_raid_start(message: Message, state: FSMContext):
    # Получаем последние 10 рейдов из БД, отсортированных по времени (сначала новые)
    raids = session.query(RaidEvent).order_by(RaidEvent.start_time.desc()).limit(10).all()

    if not raids:
        # Если рейдов нет — сообщаем об этом
        await safe_answer(message, "❌ Нет рейдов для удаления.")
        return

    # Словарь для привязки статуса рейда к иконке
    status_icon = {
        "active": "🟢 Активен",
        "finished": "✅ Завершён",
        "cancelled": "❌ Отменён"
    }

    # Формируем список рейдов в виде строк
    lines = ["📋 <b>Последние рейды:</b>\n"]
    for r in raids:
        dt = r.start_time.strftime('%d.%m %H:%M')  # Форматируем время старта
        lines.append(f"• <b>ID {r.id}</b>: {r.name} | {r.squad}\n"
                     f"  🕔 {dt} | Статус: {status_icon.get(r.status, '❓')}")

    # Добавляем инструкцию пользователю
    lines.append("\n✍️ Введите <b>ID</b> рейда для удаления или нажмите «Отмена».")

    # Устанавливаем состояние ожидания ID рейда
    await state.set_state(DeleteRaid.awaiting_raid_id)
    # Сохраняем информацию о том, откуда пришли (для возврата в меню)
    await state.update_data(from_menu="raid_admin")
    # Отправляем сформированный текст пользователю
    await safe_answer(message, "\n".join(lines), parse_mode="HTML", reply_markup=cancel_keyboard())


@router.message(F.text.lower() == "отмена")
async def cancel_deletion(message: Message, state: FSMContext):
    # Обработчик кнопки "Отмена"
    await safe_answer(message, "❌ Действие отменено.")
    # Возвращаем пользователя обратно в меню администратора
    await return_to_raid_admin_menu(message, state)


@router.message(DeleteRaid.awaiting_raid_id)
async def delete_raid_by_id(message: Message, state: FSMContext):
    # Проверяем, что введённый текст — число
    text = message.text.strip()
    if not text.isdigit():
        await safe_answer(message, "⚠️ Введите числовой ID.")
        return

    # Преобразуем введённый ID в целое число
    raid_id = int(text)
    # Ищем рейд в БД
    raid = session.query(RaidEvent).filter_by(id=raid_id).first()

    if not raid:
        # Если рейд не найден — сообщаем об этом
        await safe_answer(message, "❌ Рейд не найден.")
        await state.clear()
        return

    # Удаляем рейд из БД
    session.delete(raid)
    session.commit()

    # Сообщаем об успешном удалении
    await safe_answer(message, f"🗑 Рейд <b>{raid.name}</b> успешно удалён.", parse_mode="HTML")
    # Очищаем состояние
    await state.clear()
    # Возвращаемся в меню администратора
    await return_to_raid_admin_menu(message)
