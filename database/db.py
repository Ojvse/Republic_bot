from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Создание движка базы данных
engine = create_engine("sqlite:///db_data/bot.db", echo=False)


# Создание базового класса для моделей
Base = declarative_base()

# Создание фабрики сессий
SessionLocal = sessionmaker(bind=engine)

# Создание экземпляра сессии
session = SessionLocal()
