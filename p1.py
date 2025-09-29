#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shlex
import argparse
from typing import List, Dict, Callable, Optional

# Импортируем классы из отдельного файла VFS
from vfsEmulator import VirtualFileSystem, VFSNode

class ShellEmulator:
    """Класс эмулятора командной оболочки UNIX-подобной системы"""
    
    def __init__(self, vfs_path: str = None, debug: bool = False):
        # Инициализация словаря команд
        self.commands: Dict[str, Callable] = {
            'ls': self._cmd_ls,
            'cd': self._cmd_cd,
            'exit': self._cmd_exit,
            'pwd': self._cmd_pwd,
            'echo': self._cmd_echo,
            'debug': self._cmd_debug,
            'cat': self._cmd_cat,
            'find': self._cmd_find,
            'tree': self._cmd_tree
        }
        
        # Инициализация VFS из отдельного модуля
        self.vfs = VirtualFileSystem(debug=debug)
        self.vfs_path = vfs_path
        self.debug_mode = debug
        self.use_vfs = bool(vfs_path)  # Флаг использования VFS
        
        # Загружаем VFS если указан путь к CSV файлу
        if vfs_path and os.path.exists(vfs_path):
            self.vfs.load_from_csv(vfs_path)
            if debug:
                print(f"[DEBUG] VFS загружена из: {vfs_path}")
        elif vfs_path:
            if debug:
                print(f"[DEBUG] Файл VFS не найден: {vfs_path}")
        
        # Текущая рабочая директория ОС (для fallback когда VFS не используется)
        self.current_dir = os.getcwd()
    
    def get_prompt(self) -> str:
        """Формирует приглашение командной строки с учетом VFS"""
        username = os.getenv('USER') or os.getenv('USERNAME') or 'user'
        hostname = os.uname().nodename if hasattr(os, 'uname') else 'localhost'
        
        if self.use_vfs:
            # Используем путь из VFS для приглашения
            current_path = self.vfs.get_current_path()
            display_path = current_path if current_path != '/' else '~'
        else:
            # Используем путь из реальной ОС для приглашения
            home_dir = os.path.expanduser('~')
            if self.current_dir.startswith(home_dir):
                display_path = '~' + self.current_dir[len(home_dir):]
            else:
                display_path = self.current_dir
        
        return f"{username}@{hostname}:{display_path}$ "
    
    def parse_command(self, command_line: str) -> List[str]:
        """Парсит командную строку, корректно обрабатывая кавычки"""
        try:
            return shlex.split(command_line)
        except ValueError as e:
            print(f"Ошибка парсинга: {e}")
            return []
    
    # Команды эмулятора с поддержкой VFS
    
    def _cmd_ls(self, args: List[str]) -> int:
        """Команда ls - выводит содержимое директории (VFS или реальной ОС)"""
        path = args[0] if args else ""
        
        if self.use_vfs:
            # Работа с виртуальной файловой системой
            items = self.vfs.list_directory(path)
            if items is None:
                print(f"ls: невозможно получить доступ к '{path}': Нет такого файла или каталога")
                return 1
            
            # Выводим содержимое директории в формате ls -l
            for item in items:
                type_indicator = 'd' if item['type'] == 'directory' else '-'
                size = item['size']
                print(f"{type_indicator}rw-r--r-- 1 user user {size:6} {item['name']}")
        else:
            # Fallback к реальной файловой системе ОС
            target_path = os.path.join(self.current_dir, path) if path else self.current_dir
            try:
                for item in os.listdir(target_path):
                    item_path = os.path.join(target_path, item)
                    if os.path.isdir(item_path):
                        print(f"d {item}/")
                    else:
                        print(f"- {item}")
            except FileNotFoundError:
                print(f"ls: невозможно получить доступ к '{path}': Нет такого файла или каталога")
                return 1
        
        return 0
    
    def _cmd_cd(self, args: List[str]) -> int:
        """Команда cd - изменяет текущую директорию (VFS или реальную)"""
        if not args:
            target = "~"
        else:
            target = args[0]
        
        if self.use_vfs:
            # Работа с виртуальной файловой системой
            success = self.vfs.change_directory(target)
            if not success:
                print(f"cd: {target}: Нет такого файла или каталога")
                return 1
        else:
            # Fallback к реальной файловой системе ОС
            if target == "~":
                target = os.path.expanduser('~')
            elif target == "..":
                target = os.path.dirname(self.current_dir)
            
            try:
                os.chdir(target)
                self.current_dir = os.getcwd()
            except FileNotFoundError:
                print(f"cd: {target}: Нет такого файла или каталога")
                return 1
        
        return 0
    
    def _cmd_pwd(self, args: List[str]) -> int:
        """Команда pwd - показывает текущую директорию"""
        if self.use_vfs:
            current_path = self.vfs.get_current_path()
            print(current_path if current_path != '/' else '/')
        else:
            print(self.current_dir)
        return 0
    
    def _cmd_cat(self, args: List[str]) -> int:
        """Команда cat - выводит содержимое файла"""
        if not args:
            print("cat: отсутствуют операнды")
            return 1
        
        for file_path in args:
            if self.use_vfs:
                # Чтение файла из VFS
                content = self.vfs.read_file(file_path)
                if content is None:
                    print(f"cat: {file_path}: Нет такого файла или каталога")
                    return 1
                print(content)
            else:
                # Чтение файла из реальной ОС
                try:
                    with open(file_path, 'r') as f:
                        print(f.read())
                except FileNotFoundError:
                    print(f"cat: {file_path}: Нет такого файла или каталога")
                    return 1
        
        return 0
    
    def _cmd_find(self, args: List[str]) -> int:
        """Команда find - поиск файлов по имени в VFS"""
        if not self.use_vfs:
            print("find: команда доступна только при работе с VFS")
            return 1
        
        if len(args) < 1:
            print("find: недостаточно аргументов")
            return 1
        
        search_name = args[0]
        start_path = args[1] if len(args) > 1 else "."
        
        # Используем метод find_files из класса VFS
        results = self.vfs.find_files(search_name, start_path)
        
        if not results:
            print(f"Файлы содержащие '{search_name}' не найдены")
            return 0
        
        for result in results:
            print(result)
        
        return 0
    
    def _cmd_tree(self, args: List[str]) -> int:
        """Команда tree - показывает дерево директорий VFS"""
        if not self.use_vfs:
            print("tree: команда доступна только при работе с VFS")
            return 1
        
        start_path = args[0] if args else "."
        
        def print_tree(node: VFSNode, prefix: str = "", is_last: bool = True):
            """Рекурсивная функция для отображения дерева директорий"""
            connector = "└── " if is_last else "├── "
            print(prefix + connector + node.name)
            
            if node.is_directory:
                new_prefix = prefix + ("    " if is_last else "│   ")
                children = list(node.children.values())
                for i, child in enumerate(children):
                    print_tree(child, new_prefix, i == len(children) - 1)
        
        start_node = self.vfs.get_directory_tree(start_path)
        if not start_node:
            print(f"tree: '{start_path}': Нет такого файла или каталога")
            return 1
        
        print_tree(start_node)
        return 0
    
    def _cmd_exit(self, args: List[str]) -> int:
        """Команда exit - завершает работу эмулятора"""
        print("Выход из эмулятора командной строки")
        return -1
    
    def _cmd_echo(self, args: List[str]) -> int:
        """Команда echo - выводит аргументы"""
        print(' '.join(args))
        return 0
    
    def _cmd_debug(self, args: List[str]) -> int:
        """Команда debug - показывает отладочную информацию"""
        print(f"Режим отладки: {'включен' if self.debug_mode else 'выключен'}")
        print(f"VFS путь: {self.vfs_path}")
        print(f"Использование VFS: {'да' if self.use_vfs else 'нет'}")
        if self.use_vfs:
            print(f"Текущий путь VFS: {self.vfs.get_current_path()}")
        else:
            print(f"Текущая директория ОС: {self.current_dir}")
        return 0
    
    def execute_command(self, command: str, args: List[str]) -> int:
        """Выполняет команду и возвращает код завершения"""
        if command in self.commands:
            if self.debug_mode:
                print(f"[DEBUG] Выполнение команды: {command} {args}")
            return self.commands[command](args)
        else:
            print(f"Команда не найдена: {command}")
            return 1
    
    def run_interactive(self):
        """Интерактивный режим работы эмулятора"""
        print("Добро пожаловать в эмулятор командной строки UNIX!")
        print("Доступные команды: ls, cd, pwd, echo, debug, cat, find, tree, exit")
        if self.use_vfs:
            print("Режим: VFS активирована")
        else:
            print("Режим: реальная файловая система")
        print("Для выхода введите 'exit'")
        print("-" * 50)
        
        while True:
            try:
                prompt = self.get_prompt()
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                
                parsed_args = self.parse_command(user_input)
                if not parsed_args:
                    continue
                
                command = parsed_args[0]
                args = parsed_args[1:]
                
                result = self.execute_command(command, args)
                
                if result == -1:
                    break
                    
            except KeyboardInterrupt:
                print("\nДля выхода введите 'exit'")
            except EOFError:
                print("\nВыход...")
                break
            except Exception as e:
                print(f"Неожиданная ошибка: {e}")
    
    def run_script(self, script_path: str):
        """Выполняет команды из скрипта"""
        if not os.path.exists(script_path):
            print(f"Ошибка: файл скрипта не найден: {script_path}")
            return
        
        if self.debug_mode:
            print(f"[DEBUG] Выполнение скрипта: {script_path}")
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print(f"=== ВЫПОЛНЕНИЕ СКРИПТА {script_path} ===")
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Пропускаем пустые строки и комментарии
                if not line or line.startswith('#'):
                    if self.debug_mode and line.startswith('#'):
                        print(f"[DEBUG] Пропуск комментария: {line}")
                    continue
                
                # Отображаем ввод (имитация пользовательского ввода)
                prompt = self.get_prompt()
                print(f"{prompt}{line}")
                
                # Парсим и выполняем команду
                parsed_args = self.parse_command(line)
                if not parsed_args:
                    continue
                
                command = parsed_args[0]
                args = parsed_args[1:]
                
                result = self.execute_command(command, args)
                
                if result == -1:
                    print("Завершение выполнения скрипта по команде exit")
                    break
                    
        except Exception as e:
            print(f"Ошибка выполнения скрипта: {e}")

def parse_arguments():
    """Парсит аргументы командной строки для эмулятора"""
    parser = argparse.ArgumentParser(
        description='Эмулятор командной строки UNIX-подобной системы с поддержкой VFS',
        epilog='Пример: python shell_emulator.py --vfs vfs.csv --script startup.sh --debug'
    )
    
    parser.add_argument(
        '--vfs', 
        dest='vfs_path',
        help='Путь к CSV файлу виртуальной файловой системы'
    )
    
    parser.add_argument(
        '--script', 
        dest='script_path',
        help='Путь к стартовому скрипту для выполнения команд'
    )
    
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='Включить режим отладки с подробным выводом'
    )
    
    parser.add_argument(
        '--command', 
        dest='command',
        help='Выполнить одну команду и завершить работу'
    )
    
    return parser.parse_args()

def main():
    """Точка входа в приложение эмулятора"""
    args = parse_arguments()
    
    # Выводим отладочную информацию о параметрах
    if args.debug:
        print("=== ПАРАМЕТРЫ ЗАПУСКА ЭМУЛЯТОРА ===")
        print(f"VFS путь: {args.vfs_path}")
        print(f"Путь к скрипту: {args.script_path}")
        print(f"Режим отладки: {args.debug}")
        print(f"Команда: {args.command}")
        print("=" * 40)
        print()
    
    # Создаем экземпляр эмулятора с VFS поддержкой
    shell = ShellEmulator(vfs_path=args.vfs_path, debug=args.debug)
    
    # Обрабатываем различные режимы запуска
    if args.command:
        # Режим выполнения одной команды
        parsed_args = shell.parse_command(args.command)
        if parsed_args:
            shell.execute_command(parsed_args[0], parsed_args[1:])
    elif args.script_path:
        # Режим выполнения скрипта
        shell.run_script(args.script_path)
    else:
        # Интерактивный режим
        shell.run_interactive()

if __name__ == "__main__":
    main()