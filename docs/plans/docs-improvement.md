# Documentation improvement plan

## Context

Текущая документация python-emails — одна длинная страница с примерами кода и минимумом пояснительного текста. Нет API Reference, нет Quickstart с повествованием, нет FAQ. Эталон для сравнения — документация requests (https://requests.readthedocs.io/).

Известные проблемы в текущей документации:
- `docs/transformations.rst` вызывает `emails.loader.from_zipfile(...)`, а реальная функция называется `from_zip()` — пример не работает
- Раздел "See also" ссылается на заброшенные проекты (flask-mail — 2014, marrow.mailer — 2019)

## Goal

Довести документацию до уровня, при котором пользователь может:
- быстро начать использовать библиотеку (Quickstart)
- найти описание публичного API: `Message`, `SMTPResponse`, loaders, templates, `DjangoMessage`, DKIM, exceptions (API Reference)
- решить типовые задачи без чтения исходников (Advanced Usage, FAQ)

## Phase 0: Исправить существующие ошибки

Перед написанием нового контента — привести в порядок то, что уже есть.

- [x] Исправить `from_zipfile()` → `from_zip()` в `docs/transformations.rst`
- [x] Проверить все примеры кода на соответствие текущему API (grep по именам функций в docs/ vs реальный код)
- [x] Убрать мёртвые ссылки из "See also"

## Phase 1: API Reference

Ручной RST-файл `docs/api.rst` с описанием публичного API. Включается в `index.rst` через `.. include::`.

Scope: синхронный публичный API. Async API (если/когда появится) документируется отдельно.

- [x] Секция **Message** — конструктор, все параметры: `html`, `text`, `subject`, `mail_from`, `mail_to`, `cc`, `bcc`, `reply_to`, `headers`, `headers_encoding`, `attachments`, `charset`, `message_id`, `date`
- [x] Секция **Message methods** — `send()`, `attach()`, `render()`, `as_string()`, `as_bytes()`, `as_message()`, `transform()`, `dkim()`/`sign()`
- [x] Секция **Message properties** — `html`, `text`, `html_body`, `text_body`, `mail_from`, `mail_to`, `cc`, `bcc`, `reply_to`, `subject`, `message_id`, `date`, `charset`, `headers_encoding`, `attachments`, `transformer`, `render_data`
- [x] Секция **SMTPResponse** — `status_code`, `status_text`, `success`, `error`, `refused_recipients`, `last_command`
- [x] Секция **Loaders** — `from_url()`, `from_html()`, `from_directory()`, `from_zip()`, `from_file()`, `from_rfc822()`. Упомянуть алиасы `from_string` = `from_html`, `load_url` = `from_url` (не документировать как отдельные функции)
- [x] Секция **Loader exceptions** — `LoadError`, `IndexFileNotFound`, `InvalidHtmlFile`
- [x] Секция **Templates** — `JinjaTemplate`, `StringTemplate`, `MakoTemplate`
- [x] Секция **DjangoMessage** — отличия от `Message`, метод `send()`, параметр `context`
- [x] Секция **DKIM** — параметры `dkim(key=, domain=, selector=)`
- [x] Секция **Exceptions** — `HTTPLoaderError`, `BadHeaderError`, `IncompleteMessage` + loader exceptions (ссылка на секцию выше)
- [x] Секция **Utilities** — `MessageID`, `emails.html()`
- [x] Включить `api.rst` в `index.rst`
- [x] Проверить сборку `make html` без ошибок

## Phase 2: Quickstart

Переписать раздел Examples в повествовательном стиле. Файл `docs/quickstart.rst`, заменяет текущий `examples.rst` в `index.rst`.

- [x] Вступление — что делает библиотека, для кого, чем лучше smtplib
- [x] Создание простого письма — `emails.html()`, пояснение параметров
- [x] Отправка письма — `message.send()`, объяснение `smtp` dict, проверка `response.status_code`
- [x] Вложения — `attach()` с пояснением `content_disposition`
- [x] Inline-картинки — как работает `cid:`, пример
- [x] Шаблоны — `JinjaTemplate`, `render={}`, зачем нужны
- [x] DKIM-подпись — зачем, как подключить
- [x] Генерация без отправки — `as_string()`, `as_message()`
- [x] Обработка ошибок — что возвращает `send()`, как обрабатывать отказы
- [x] Заменить `examples.rst` на `quickstart.rst` в `index.rst`

## Phase 3: Advanced Usage

Новый файл `docs/advanced.rst` с продвинутыми сценариями.

- [x] SMTP-соединения — переиспользование backend, таймауты, SSL vs TLS
- [x] HTML-трансформации — подробно про `transform()`, актуальные параметры: `css_inline`, `remove_unsafe_tags`, `set_content_type_meta`, `load_images`, `images_inline`. Явно указать deprecated: `make_links_absolute=False` (premailer всегда делает absolute), `update_stylesheet=True` (premailer не поддерживает)
- [x] Custom link/image transformations — `transformer.apply_to_images()`, `apply_to_links()`
- [x] Loaders — загрузка из URL, ZIP, директории, .eml; когда использовать какой
- [x] Django-интеграция — `DjangoMessage`, настройка backend, пример с `context`
- [x] Flask-интеграция — ссылка на flask-emails, пример
- [x] Кодировки и charset — когда менять, IDN-домены
- [x] Заголовки — кастомные headers, `Reply-To`, `CC`, `BCC`
- [x] Включить `advanced.rst` в `index.rst`

## Phase 4: Улучшение главной страницы и темы

Перейти с alabaster на Furo — современная тема, используется urllib3, attrs, pytest. Responsive, тёмная тема, нормальная ширина из коробки, не нужны CSS-хаки.

- [x] Заменить тему на Furo: `pip install furo`, `html_theme = "furo"` в conf.py
- [x] Удалить `_themes/` (локальные копии alabaster/flask больше не нужны)
- [x] Удалить `conf_theme_alabaster.py` и `conf_theme_flask.py`, перенести нужные настройки в conf.py
- [x] Настроить `html_theme_options` для Furo: sidebar, навигация, ссылки на GitHub/PyPI
- [x] Добавить `furo` в `docs/requirements.txt`
- [x] Добавить badges (PyPI version, Python versions, license)
- [x] Обновить вводный пример — сделать проще и нагляднее
- [x] Добавить список фич в стиле requests ("Beloved Features")
- [x] Обновить раздел "How to Help" — убрать "under development", добавить ссылку на issues
- [x] Проверить сборку и внешний вид на ReadTheDocs

## Phase 5: FAQ

Новый файл `docs/faq.rst`.

Принцип для провайдер-специфичных вопросов: давать только общие SMTP-параметры (`host`, `port`, `ssl`/`tls`) + ссылку на официальную документацию провайдера. Не дублировать инструкции провайдера — они меняются вне этого репозитория.

- [x] Как отправить через Gmail / Yandex / другой провайдер — общий шаблон `smtp={...}` + ссылки на офиц. доки
- [x] Как приложить PDF / Excel
- [x] Чем отличается от smtplib + email.mime — перенести stdlib-пример из gist в документацию под collapsible-блок (сейчас внешняя ссылка "the same code, without Emails")
- [x] Чем отличается от django.core.mail
- [x] Как отладить отправку (debug, logging)
- [x] Включить `faq.rst` в `index.rst`

## Phase 5b: Обновить "See also" — сравнение с альтернативами

Заменить текущий список (premailer, flask-mail, marrow.mailer) на актуальных живых конкурентов. Для каждого — краткое описание и чем python-emails отличается.

Библиотеки для сравнения:
- **smtplib + email** — стандартная библиотека
- **yagmail** — самый популярный конкурент
- **red-mail** — современный, с шаблонами и embedded images
- **envelope** — с GPG/S/MIME шифрованием

Убрать из текущего "See also":
- premailer (зависимость, не альтернатива — перенести в acknowledgements)
- marrow.mailer (заброшена с 2019)

Принцип: не фиксировать в документации утверждения "у X нет фичи Y" без проверки. Сравнение строить от сильных сторон python-emails, а не от слабых сторон конкурентов.

- [x] Проверить актуальные фичи каждой библиотеки перед написанием сравнения
- [x] Переписать `links.rst` с актуальными альтернативами и кратким сравнением
- [x] Упомянуть premailer как зависимость, а не альтернативу

## Phase 5c: Автоматическая проверка примеров

Одноразовый grep из Phase 0 не защищает от повторного дрейфа. Нужна автоматика в CI.

- [x] Включить `sphinx.ext.doctest` — примеры с `>>>` в RST будут проверяться через `make doctest`
- [x] Перевести интерактивные примеры (transformations.rst уже использует `>>>`) на формат doctest
- [x] Добавить `make linkcheck` для проверки внешних ссылок
- [x] Добавить шаг `make doctest && make linkcheck` в CI (GitHub Actions)

## Phase 6: Разбиение на подстраницы

Когда контент вырастет, заменить `.. include::` на `.. toctree::` для навигации между страницами.

- [x] Заменить `include` на `toctree` в `index.rst`
- [x] Проверить навигацию и перекрёстные ссылки
- [x] Проверить сборку

## Explicit limitations

- Autodoc не используется — docstrings в коде минимальны, API Reference пишется вручную
- Документация остаётся на одной странице до Phase 6
- Язык документации — английский
- Провайдер-специфичные инструкции (Gmail, Yandex) — только SMTP-параметры + ссылки, не полные гайды
