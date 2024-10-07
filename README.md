# Ozon Product Scraper API

Это FastAPI-сервер для скрапинга информации о продуктах с Ozon.ru. Сервер предоставляет API-endpoint для поиска продуктов и возвращает подробную информацию о найденных товарах.

## Требования

- Python 3.7+
- pip (менеджер пакетов Python)

## Установка

1. Клонируйте репозиторий или скачайте исходный код.

2. Перейдите в директорию проекта:
   ```
   cd path/to/ozon-scraper
   ```

3. (Рекомендуется) Создайте и активируйте виртуальное окружение:
   ```
   python -m venv venv
   source venv/bin/activate  # Для Windows используйте: venv\Scripts\activate
   ```

4. Установите необходимые зависимости:
   ```
   pip install -r requirements.txt
   ```

5. Установите браузеры для Playwright:
   ```
   playwright install
   ```

## Настройка

Настройки сервера находятся в файле `config.py`. По умолчанию сервер запускается на `0.0.0.0:8000`. Вы можете изменить эти настройки, отредактировав `config.py`:

```python
HOST = "0.0.0.0"  # Измените на "localhost" для локального доступа
PORT = 8000  # Измените порт по необходимости
```

## Запуск сервера

Для запуска сервера выполните следующую команду:

```
python server.py
```

Сервер будет доступен по адресу `http://localhost:8000` (или по IP и порту, указанным в `config.py`).

## Использование API

### Поиск продуктов

Для поиска продуктов отправьте POST-запрос на endpoint `/search`:

```bash
curl -X POST "http://localhost:8000/search" \
     -H "Content-Type: application/json" \
     -d '{"query": "мыло"}'
```

Этот запрос вернет JSON с результатами поиска, включая информацию о продуктах.

## Проверка работы

1. Убедитесь, что сервер запущен.

2. Откройте новый терминал и выполните curl-запрос (пример выше).

3. Вы должны получить JSON-ответ с результатами поиска. Пример ответа:

```json
{
  "results": [
    {
      "product_id": "123456",
      "short_name": "Мыло детское",
      "full_name": "Мыло детское с экстрактом ромашки",
      "description": "Нежное мыло для чувствительной кожи",
      "url": "https://www.ozon.ru/product/123456",
      "price": "50 RUB",
      "price_with_card": "45 ₽",
      "image_url": "https://cdn1.ozone.ru/s3/multimedia-3/123456.jpg"
    },
    // Дополнительные результаты...
  ]
}
```

4. Если вы получили подобный ответ, значит сервер работает корректно.

## Устранение неполадок

- Если сервер не запускается, проверьте, что все зависимости установлены корректно.
- Убедитесь, что порт, указанный в `config.py`, не занят другим процессом.
- При ошибках в работе скрапера проверьте подключение к интернету и доступность сайта Ozon.ru.
