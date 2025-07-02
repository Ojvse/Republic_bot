from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    game_id = Column(Integer, unique=True, index=True)
    nickname = Column(String)
    faction = Column(String)
    squad = Column(String)
    role = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_admin = Column(Boolean, default=False)

class RaidEvent(Base):
    __tablename__ = "raid_events"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    squad = Column(String)
    start_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="active")
    location_id = Column(Integer, ForeignKey("location_info.id"), nullable=True)
    location = relationship("LocationInfo")

    # Каскадные связи
    participations = relationship("RaidParticipation", cascade="all, delete-orphan", backref="raid")
    reminders = relationship("RaidReminder", cascade="all, delete-orphan", backref="raid")
    pin_logs = relationship("RaidPinSendLog", cascade="all, delete-orphan", backref="raid")

class RaidParticipation(Base):
    __tablename__ = "raid_participation"
    id = Column(Integer, primary_key=True)
    raid_id = Column(Integer, ForeignKey("raid_events.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id"))
    joined_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String)

class RaidReminder(Base):
    __tablename__ = "raid_reminders"
    id = Column(Integer, primary_key=True)
    raid_id = Column(Integer, ForeignKey("raid_events.id", ondelete="CASCADE"))
    user_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class RaidPinSendLog(Base):
    __tablename__ = "raid_pin_send_logs"
    id = Column(Integer, primary_key=True)
    admin_id = Column(Integer, ForeignKey("users.id"))
    target_id = Column(Integer, ForeignKey("users.id"))
    raid_id = Column(Integer, ForeignKey("raid_events.id", ondelete="CASCADE"), nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    pin_text = Column(String)

class RaidPinData(Base):
    __tablename__ = "raid_pin_data"

    id = Column(Integer, primary_key=True)
    raid_id = Column(Integer, ForeignKey("raid_events.id", ondelete="CASCADE"), unique=True)
    title = Column(String)
    km = Column(Integer)
    description = Column(String)

class PlayerProfile(Base):

    __tablename__ = "player_profiles"

    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, unique=True, index=True)  # Уникальный игровой ID
    nickname = Column(String)                           # Никнейм игрока
    faction = Column(String)                            # Фракция
    squad = Column(String)                              # Отряд
    added_by_admin = Column(Boolean, default=False)     # Добавлен ли игрок администратором
    added_by_admin_id = Column(Integer, nullable=True)  # ID администратора, добавившего игрока

    health_current = Column(Integer)                    # Текущее здоровье
    health_max = Column(Integer)                        # Максимальное здоровье
    hunger = Column(Integer)                            # Голод
    damage = Column(Integer)                            # Урон
    armor = Column(Integer)                             # Броня

    strength = Column(Integer)                          # Сила
    accuracy = Column(Integer)                          # Точность
    charisma = Column(Integer)                          # Харизма
    agility = Column(Integer)                           # Ловкость
    stamina_current = Column(Integer)                   # Текущая выносливость
    stamina_max = Column(Integer)                       # Максимальная выносливость

    location = Column(String)                           # Текущее местоположение
    distance_km = Column(Integer)                       # Расстояние до цели
    gear = Column(String)                               # Оборудование

    caps = Column(Integer)                              # Капы (денежная единица)
    materials = Column(Integer)                         # Материалы
    bobbleheads = Column(Integer)                       # Боблы (награды)

    reputation = Column(String)                         # Репутация

    raid_time = Column(String)                          # Время последнего рейда
    raid_location = Column(String)                      # Место последнего рейда
    raid_reward_caps = Column(Integer)                  # Награда капами
    raid_reward_materials = Column(Integer)             # Награда материалами
    raid_reward_other = Column(String)                  # Другие награды

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # Дата последнего обновления


class GuidePage(Base):

    __tablename__ = "guide_pages"

    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, index=True)      # Уникальный код страницы (например, s_0, eq_1)
    title = Column(String)                              # Заголовок страницы
    text = Column(String, nullable=True)                # Текст содержания (если это конечная страница)
    parent_code = Column(String, nullable=True)         # Код родительской страницы (если есть)
    created_at = Column(DateTime, default=datetime.utcnow)  # Дата создания


class LocationInfo(Base):

    __tablename__ = "location_info"

    id = Column(Integer, primary_key=True)
    km = Column(Integer, unique=True, index=True)       # Расстояние в километрах
    title = Column(String)                              # Название локации
    description = Column(String)                        # Описание локации
