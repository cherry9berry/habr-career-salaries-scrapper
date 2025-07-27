#!/usr/bin/env python3
"""
Скрипт для проверки секретов в коде
Использование: python scripts/check-secrets.py
"""

import re
import os
import sys
from pathlib import Path

# Паттерны для поиска РЕАЛЬНЫХ секретов (исключая примеры)
SECRET_PATTERNS = [
    (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API ключ'),
    (r'ghp_[a-zA-Z0-9]{36}', 'GitHub токен'),
    (r'xoxb-[0-9]{11,12}-[0-9]{11,12}-[a-zA-Z0-9]{24}', 'Slack токен'),
    (r'[a-zA-Z0-9]{32,}', 'Подозрительно длинная строка'),
]

# Исключения из проверки
EXCLUDE_DIRS = {'.git', '__pycache__', '.pytest_cache', '.mypy_cache', 'node_modules', '.ruff_cache', '.coverage'}
EXCLUDE_FILES = {'check-secrets.py', 'pre-commit', 'CACHEDIR.TAG', '.coverage', 'coverage.xml'}

# Файлы с примерами - проверяем только критичные паттерны
EXAMPLE_FILES = {'config.example.yaml', 'README.md', 'docker-compose.yml', 'render_setup.sh'}

# Безопасные значения-примеры (не настоящие секреты)
SAFE_EXAMPLES = {
    'your_password',
    'your_secure_password',
    'password',
    'secret',
    'token',
    'your_api_key',
    'your_secret',
    'your_token',
    'example_password',
    '8a477f597d28d172789f06886806bc55',  # ruff cache hash
}


def check_file(file_path):
    """Проверить файл на наличие секретов"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        findings = []
        file_name = os.path.basename(str(file_path))

        for pattern, description in SECRET_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                matched_text = match.group()

                # Пропускаем примеры и плейсхолдеры
                if any(safe in matched_text.lower() for safe in SAFE_EXAMPLES):
                    continue

                # Для файлов-примеров проверяем только критичные паттерны
                if file_name in EXAMPLE_FILES and 'API ключ' not in description and 'токен' not in description:
                    continue

                line_num = content[: match.start()].count('\n') + 1
                findings.append(
                    {
                        'file': file_path,
                        'line': line_num,
                        'pattern': description,
                        'match': matched_text[:50] + '...' if len(matched_text) > 50 else matched_text,
                    }
                )

        return findings
    except Exception:
        return []


def main():
    """Основная функция"""
    print("🔍 Поиск секретов в проекте...")

    all_findings = []
    project_root = Path('.')

    for root, dirs, files in os.walk(project_root):
        # Исключаем системные директории
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            if file in EXCLUDE_FILES:
                continue

            file_path = Path(root) / file
            findings = check_file(file_path)
            all_findings.extend(findings)

    if all_findings:
        print(f"\n🚨 НАЙДЕНО {len(all_findings)} потенциальных секретов:")
        print("-" * 60)

        for finding in all_findings:
            print(f"📁 {finding['file']}:{finding['line']}")
            print(f"🔍 {finding['pattern']}")
            print(f"📝 {finding['match']}")
            print("-" * 60)

        print("\n🔧 Рекомендации:")
        print("1. Удалите секреты из файлов")
        print("2. Используйте переменные окружения")
        print("3. Добавьте файлы с секретами в .gitignore")
        print("4. Используйте config.example.yaml для примеров")

        sys.exit(1)
    else:
        print("✅ Секреты не найдены!")
        sys.exit(0)


if __name__ == "__main__":
    main()
