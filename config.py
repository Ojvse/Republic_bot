import os
import ast
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# Токен бота, полученный из переменной окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Список ID администраторов, полученный из переменной окружения
ADMIN_IDS = ast.literal_eval(os.getenv("ADMIN_IDS", "[]"))

