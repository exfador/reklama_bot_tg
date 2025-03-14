# Рекламный бот

Телеграм-бот для отправки рекламных сообщений по расписанию.

## Установка и настройка

### Шаг 1: Установка зависимостей

```bash
pip install -r requirements.txt
```

### Шаг 2: Настройка конфигурации

1. Откройте файл `config.py`
2. Вставьте ваш токен бота в переменную `BOT_TOKEN`:

```python
BOT_TOKEN: str = "ваш_токен_бота"  
```

3. При необходимости измените другие параметры:
   - `DB_PATH` - путь к базе данных (по умолчанию "database/reklama.db")
   - `MIN_INTERVAL` и `MAX_INTERVAL` - минимальный и максимальный интервал между сообщениями (в минутах)
   - `MIN_DURATION` и `MAX_DURATION` - минимальная и максимальная продолжительность рекламы (в минутах)

### Шаг 3: Запуск бота

```bash
python main.py
```

## Структура проекта

- `main.py` - главный файл для запуска бота
- `config.py` - конфигурационный файл
- `database/` - директория с файлами базы данных
- `handlers/` - обработчики сообщений
- `keyboards/` - клавиатуры и кнопки
- `middlewares/` - промежуточные обработчики
- `utils/` - вспомогательные функции

## Получение токена бота

1. Откройте Telegram и найдите @BotFather
2. Отправьте команду `/newbot`
3. Следуйте инструкциям, чтобы создать нового бота
4. После создания бота вы получите токен - скопируйте его в файл `config.py`

## Работа с ботом

После запуска бота вы можете взаимодействовать с ним в Telegram, используя команды и интерфейс для настройки рекламных сообщений.

## Обслуживание

База данных автоматически создается при первом запуске бота. Данные хранятся в файле, указанном в `DB_PATH`.

## Системные требования

- Python 3.7 или выше
- Доступ к интернету для работы с Telegram API 