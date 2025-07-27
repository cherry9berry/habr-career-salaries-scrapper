#!/usr/bin/env python3
"""
Скрипт для проверки секретов в коде
Использование: python scripts/check-secrets.py
"""

import re
import os
import sys
from pathlib import Path

# Паттерны для поиска секретов
SECRET_PATTERNS = [
    (r'!!!!QQQQ\d+', 'Supabase пароль'),
    (r'password\s*[:=]\s*["\'][^"\']{8,}["\']', 'Пароль в кавычках'),
    (r'PASSWORD\s*[:=]\s*[^\s]+', 'Пароль в переменной окружения'),
    (r'api[_-]?key\s*[:=]\s*["\'][^"\']+["\']', 'API ключ'),
    (r'secret\s*[:=]\s*["\'][^"\']+["\']', 'Секрет'),
    (r'token\s*[:=]\s*["\'][^"\']+["\']', 'Токен'),
    (r'postgres\.[a-z0-9]+', 'Supabase пользователь'),
    (r'sk-[a-zA-Z0-9]{48}', 'OpenAI API ключ'),
    (r'ghp_[a-zA-Z0-9]{36}', 'GitHub токен'),
]

# Исключения из проверки
EXCLUDE_DIRS = {'.git', '__pycache__', '.pytest_cache', '.mypy_cache', 'node_modules'}
EXCLUDE_FILES = {'check-secrets.py', 'pre-commit'}

def check_file(file_path):
    """Проверить файл на наличие секретов"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        findings = []
        for pattern, description in SECRET_PATTERNS:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                findings.append({
                    'file': file_path,
                    'line': line_num,
                    'pattern': description,
                    'match': match.group()[:50] + '...' if len(match.group()) > 50 else match.group()
                })
        
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