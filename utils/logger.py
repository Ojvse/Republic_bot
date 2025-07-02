import logging


# Создание логгера для текущего модуля
logger = logging.getLogger(__name__)

# Создание обработчика вывода логов в консоль (StreamHandler)
handler = logging.StreamHandler()

# Форматирование сообщений логов: [время] уровень_лога - текст_сообщения
formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")

# Применение форматирования к обработчику
handler.setFormatter(formatter)

# Добавление обработчика к логгеру
logger.addHandler(handler)

# Установка уровня логирования: INFO и выше (INFO, WARNING, ERROR, CRITICAL)
logger.setLevel(logging.INFO)
