# Textual Code Editor

Простой TUI редактор кода на Python с подсветкой синтаксиса.

## Установка

```bash
pip install -r requirements.txt
```

## Использование

```bash
# Открыть существующий файл
python editor.py path/to/file.py

# Открыть пустой редактор
python editor.py
```

## Горячие клавиши

- `Ctrl+S` - Сохранить файл
- `Ctrl+Q` - Выйти из редактора
- `↑ ↓ ← →` - Навигация
- `Home/End` - Начало/конец строки
- `Page Up/Down` - Прокрутка страницы

## Возможности

- ✅ Открытие файлов через аргументы CLI
- ✅ Сохранение файлов (Ctrl+S)
- ✅ Подсветка синтаксиса (автоопределение по расширению файла)
- ✅ Номера строк
- ✅ Статус-бар с информацией о файле
- ✅ Индикация несохранённых изменений
- ✅ Поддержка 300+ языков через Pygments

## Примеры

```bash
# Редактировать Python файл
python editor.py main.py

# Редактировать JavaScript
python editor.py script.js

# Создать новый файл
python editor.py newfile.txt
```

## Требования

- Python 3.8+
- Textual 0.44+
- Pygments 2.16+

## Лицензия

MIT
