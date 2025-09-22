#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shlex
from typing import List, Dict, Callable

class ShellEmulator:
    """Класс эмулятора командной оболочки UNIX-подобной системы"""
    
    def __init__(self):
        # Инициализация словаря команд: ключ - имя команды, значение - функция обработки
        self.commands: Dict[str, Callable] = {
            'ls': self._cmd_ls,
            'cd': self._cmd_cd,
            'exit': self._cmd_exit
        }
        # Текущая рабочая директория
        self.current_dir = os.getcwd()
    
    def get_prompt(self) -> str:
        """Формирует приглашение командной строки в формате username@hostname:path$"""
        # Получаем имя пользователя из переменных окружения
        username = os.getenv('USER') or os.getenv('USERNAME') or 'user'
        # Получаем имя хоста
        hostname = os.uname().nodename if hasattr(os, 'uname') else 'localhost'
        
        # Получаем относительный путь от домашней директории
        home_dir = os.path.expanduser('~')
        if self.current_dir.startswith(home_dir):
            # Если находимся в домашней директории или её поддиректории, показываем ~
            display_path = '~' + self.current_dir[len(home_dir):]
        else:
            display_path = self.current_dir
        
        # Формируем итоговое приглашение
        return f"{username}@{hostname}:{display_path}$ "

    
    def parse_command(self, command_line: str) -> List[str]:
        """Парсит командную строку, корректно обрабатывая кавычки"""
        try:
            # Используем shlex для корректного парсинга аргументов с кавычками
            return shlex.split(command_line)
        except ValueError as e:
            # Обработка ошибок парсинга (например, незакрытые кавычки)
            print(f"Ошибка парсинга: {e}")
            return []
    
    def _cmd_ls(self, args: List[str]) -> int:
        """Команда ls - заглушка, выводит имя команды и аргументы"""
        print(f"Команда 'ls' вызвана с аргументами: {args}")
        # Возвращаем код завершения 0 (успех)
        return 0
    
    def _cmd_cd(self, args: List[str]) -> int:
        """Команда cd - заглушка, выводит имя команды и аргументы"""
        print(f"Команда 'cd' вызвана с аргументами: {args}")
        
        # Базовая имитация изменения директории
        if len(args) > 0:
            target_dir = args[0]
            if target_dir == '..':
                # Переход на уровень выше
                self.current_dir = os.path.dirname(self.current_dir)
            elif target_dir == '~':
                # Переход в домашнюю директорию
                self.current_dir = os.path.expanduser('~')
            else:
                # Простая имитация изменения пути
                print(f"(имитация перехода в директорию {target_dir})")
        
        # Возвращаем код завершения 0 (успех)
        return 0
    
    def _cmd_exit(self, args: List[str]) -> int:
        """Команда exit - завершает работу эмулятора"""
        print("Выход из эмулятора командной строки")
        # Возвращаем специальный код для выхода
        return -1
    
    def execute_command(self, command: str, args: List[str]) -> int:
        """Выполняет команду и возвращает код завершения"""
        if command in self.commands:
            # Вызываем соответствующую функцию команды
            return self.commands[command](args)
        else:
            # Команда не найдена
            print(f"Команда не найдена: {command}")
            return 1  # Код ошибки
    
    def run(self):
        """Основной цикл работы эмулятора"""
        print("Добро пожаловать в эмулятор командной строки UNIX!")
        print("Доступные команды: ls, cd, exit")
        print("Для выхода введите 'exit'")
        print("-" * 50)
        
        while True:
            try:
                # Выводим приглашение и читаем ввод пользователя
                prompt = self.get_prompt()
                user_input = input(prompt).strip()
                
                # Пропускаем пустые строки
                if not user_input:
                    continue
                
                # Парсим командную строку
                parsed_args = self.parse_command(user_input)
                if not parsed_args:
                    continue
                
                # Извлекаем команду и её аргументы
                command = parsed_args[0]
                args = parsed_args[1:]
                
                # Выполняем команду
                result = self.execute_command(command, args)
                
                # Проверяем, не пора ли выйти
                if result == -1:
                    break
                    
            except KeyboardInterrupt:
                # Обработка Ctrl+C
                print("\nДля выхода введите 'exit'")
            except EOFError:
                # Обработка Ctrl+D
                print("\nВыход...")
                break
            except Exception as e:
                # Обработка других неожиданных ошибок
                print(f"Неожиданная ошибка: {e}")

def main():
    """Точка входа в приложение"""
    # Создаем экземпляр эмулятора
    shell = ShellEmulator()
    
    # Запускаем основной цикл
    shell.run()

if __name__ == "__main__":
    # Запускаем приложение только если файл выполняется напрямую
    main()

#lkjlkjkl

# Демонстрация работы эмулятора
def demonstrate_shell():
    """Функция для демонстрации работы эмулятора"""
    shell = ShellEmulator()
    
    print("=== ДЕМОНСТРАЦИЯ РАБОТЫ ЭМУЛЯТОРА ===")
    print()
    
    # Тестирование приглашения командной строки
    print("1. Приглашение командной строки:")
    print(f"   {shell.get_prompt()}")
    print()
    
    # Тестирование парсера с кавычками
    print("2. Тестирование парсера:")
    test_commands = [
        'ls -l "file with spaces"',
        'cd "directory name"',
        "ls 'another file'",
        'echo "unclosed quote',
        'ls -a *.py'
    ]
    
    for cmd in test_commands:
        print(f"   Ввод: '{cmd}'")
        parsed = shell.parse_command(cmd)
        print(f"   Результат: {parsed}")
    print()
    
    # Тестирование команд
    print("3. Тестирование команд:")
    
    # Команда ls
    print("   Команда ls:")
    shell._cmd_ls(['-l', '-a', 'file.txt'])
    
    # Команда cd
    print("   Команда cd:")
    shell._cmd_cd(['..'])
    
    # Команда exit
    print("   Команда exit:")
    # shell._cmd_exit([])  # Раскомментировать для теста выхода
    
    print()
    print("=== ЗАПУСК ИНТЕРАКТИВНОГО РЕЖИМА ===")
    print("Для тестирования запустите основной скрипт")

# Запуск демонстрации
if __name__ == "__demo__":
    demonstrate_shell()