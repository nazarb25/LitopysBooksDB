# Архітектура LitopysDB

Структура наслідує поділ еталонного FastAPI-проєкту на `domain`, `application`,
`infrastructure`, `presentation` і `bootstrap`.

```text
app/
├── domain/          # сутності та доменні помилки
├── application/     # DTO, порти й окремий use case для кожної операції
├── infrastructure/  # SQLAlchemy, HTTP, PDF-парсер і файлове сховище
├── presentation/    # FastAPI API, HTML та CLI адаптери
├── bootstrap/       # побудова графа залежностей
├── cli.py           # composition root для CLI
└── main.py          # composition root для ASGI
```

Залежності спрямовані всередину:

```text
presentation ──▶ application ◀── infrastructure
                       │
                       ▼
                     domain
```

## Межі

- `domain` не імпортує фреймворки, ORM, конфігурацію або транспорт.
- `application` описує сценарії та порти й не знає про конкретні адаптери.
- `infrastructure` реалізує порти: SQLAlchemy repositories і Unit of Work,
  клієнт Книжкової палати, PDF-парсер та локальний архів.
- `presentation` перетворює HTTP/CLI ввід на application DTO і форматує результат.
- `bootstrap` є єдиним місцем, де конкретні реалізації з'єднуються між собою.

## Запис і читання

Імпорт одного випуску є транзакцією: парсинг виконується до її відкриття, а заміна
випуску й усіх записів комітиться разом. Репозиторії не викликають `commit`.
Масове оновлення структурованих полів комітиться окремими пакетами.

Пошук використовує окремий read repository. Фільтрація, підрахунок загальної
кількості, сортування й пагінація виконуються в SQL, після чого повертається
`BookSearchPageDTO`.

## Міграції

Схемою керує Alembic у `migrations/`. Infrastructure factory лише створює engine
та session factory; вона не змінює таблиці під час запуску застосунку.

## Перевірка меж

`tests/test_architecture.py` аналізує імпорти через AST та не дозволяє залежностям
перетинати внутрішні межі у зворотному напрямку.
