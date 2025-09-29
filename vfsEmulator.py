#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import base64
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

class VFSNode:
    """Класс для представления узла виртуальной файловой системы"""
    
    def __init__(self, name: str, is_directory: bool = False, content: str = "", parent=None):
        self.name = name  # Имя файла/директории
        self.is_directory = is_directory  # Флаг директории
        self.content = content  # Содержимое файла (для директорий - пустое)
        self.children = {}  # Дочерние узлы (для директорий)
        self.parent = parent  # Родительский узел
    
    def add_child(self, node: 'VFSNode'):
        """Добавляет дочерний узел к текущему узлу"""
        self.children[node.name] = node
        node.parent = self
    
    def get_path(self) -> str:
        """Возвращает полный путь к узлу в VFS"""
        if self.parent is None:
            return self.name
        return str(Path(self.parent.get_path()) / self.name)

class VirtualFileSystem:
    """Класс виртуальной файловой системы для эмулятора"""
    
    def __init__(self, debug: bool = False):
        self.root = VFSNode("", is_directory=True)  # Корневая директория VFS
        self.current_dir = self.root  # Текущая рабочая директория в VFS
        self.debug = debug  # Режим отладки
    
    def load_from_csv(self, csv_path: str):
        """Загружает структуру VFS из CSV-файла"""
        if self.debug:
            print(f"[DEBUG] Загрузка VFS из файла: {csv_path}")
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row_num, row in enumerate(reader, 1):
                    # Извлекаем данные из CSV строки
                    path = row['path'].strip()
                    is_directory = row.get('type', 'file').strip().lower() == 'directory'
                    content = row.get('content', '')
                    
                    # Декодируем base64 содержимое если указано кодирование
                    if not is_directory and row.get('encoding') == 'base64':
                        try:
                            content = base64.b64decode(content).decode('utf-8')
                        except Exception as e:
                            if self.debug:
                                print(f"[DEBUG] Ошибка декодирования base64 в строке {row_num}: {e}")
                    
                    # Создаем узлы по указанному пути
                    self._create_path(path, is_directory, content)
            
            if self.debug:
                print(f"[DEBUG] VFS успешно загружена. Узлов: {self._count_nodes(self.root)}")
                
        except Exception as e:
            print(f"Ошибка загрузки VFS: {e}")
    
    def _create_path(self, path: str, is_directory: bool, content: str = ""):
        """Создает путь в VFS, создавая все промежуточные директории"""
        parts = Path(path).parts
        current_node = self.root
        
        # Проходим по всем частям пути кроме последней (создаем директории)
        for part in parts[:-1]:
            if part not in current_node.children:
                # Создаем промежуточную директорию если ее нет
                dir_node = VFSNode(part, is_directory=True, parent=current_node)
                current_node.add_child(dir_node)
                current_node = dir_node
            else:
                current_node = current_node.children[part]
                if not current_node.is_directory:
                    # Если узел не директория, преобразуем в директорию
                    current_node.is_directory = True
                    current_node.content = ""
        
        # Создаем конечный узел (файл или директорию)
        last_part = parts[-1]
        if last_part not in current_node.children:
            new_node = VFSNode(last_part, is_directory, content, current_node)
            current_node.add_child(new_node)
        else:
            # Обновляем существующий узел
            existing_node = current_node.children[last_part]
            existing_node.is_directory = is_directory
            if not is_directory:
                existing_node.content = content
    
    def _count_nodes(self, node: VFSNode) -> int:
        """Рекурсивно подсчитывает количество узлов в VFS"""
        count = 1
        for child in node.children.values():
            count += self._count_nodes(child)
        return count
    
    def change_directory(self, path: str) -> bool:
        """Изменяет текущую директорию в VFS"""
        if path == "..":
            # Переход на уровень выше
            if self.current_dir.parent:
                self.current_dir = self.current_dir.parent
            return True
        elif path == "~" or path == "/":
            # Переход в корневую директорию
            self.current_dir = self.root
            return True
        
        # Разрешаем путь и переходим в него
        target_node = self._resolve_path(path)
        if target_node and target_node.is_directory:
            self.current_dir = target_node
            return True
        
        return False
    
    def list_directory(self, path: str = "") -> List[Dict[str, Any]]:
        """Возвращает содержимое указанной директории в VFS"""
        target_node = self._resolve_path(path) if path else self.current_dir
        
        if not target_node or not target_node.is_directory:
            return []
        
        result = []
        for name, node in target_node.children.items():
            result.append({
                'name': name,
                'type': 'directory' if node.is_directory else 'file',
                'size': len(node.content) if not node.is_directory else 0
            })
        
        # Сортируем: сначала директории, потом файлы, по алфавиту
        return sorted(result, key=lambda x: (x['type'] != 'directory', x['name']))
    
    def read_file(self, path: str) -> Optional[str]:
        """Читает содержимое файла из VFS"""
        target_node = self._resolve_path(path)
        
        if target_node and not target_node.is_directory:
            return target_node.content
        
        return None
    
    def _resolve_path(self, path: str) -> Optional[VFSNode]:
        """Разрешает путь к узлу VFS (абсолютный или относительный)"""
        if path.startswith('/'):
            # Абсолютный путь - начинаем от корня
            current_node = self.root
            path_parts = Path(path).parts[1:]  # Пропускаем корень
        else:
            # Относительный путь - начинаем от текущей директории
            current_node = self.current_dir
            path_parts = Path(path).parts
        
        # Проходим по всем частям пути
        for part in path_parts:
            if part == '.':
                # Текущая директория - пропускаем
                continue
            elif part == '..':
                # Родительская директория
                if current_node.parent:
                    current_node = current_node.parent
                else:
                    return None
            elif part in current_node.children:
                # Переходим в дочерний узел
                current_node = current_node.children[part]
            else:
                # Узел не найден
                return None
        
        return current_node
    
    def get_current_path(self) -> str:
        """Возвращает текущий путь в VFS"""
        path_parts = []
        node = self.current_dir
        
        # Собираем путь от текущей директории до корня
        while node and node != self.root:
            path_parts.append(node.name)
            node = node.parent
        
        # Формируем строку пути
        return '/' + '/'.join(reversed(path_parts)) if path_parts else '/'
    
    def find_files(self, search_name: str, start_path: str = ".") -> List[str]:
        """Рекурсивно ищет файлы по имени в VFS"""
        start_node = self._resolve_path(start_path)
        if not start_node:
            return []
        
        def search_recursive(node: VFSNode, current_path: str) -> List[str]:
            """Внутренняя рекурсивная функция поиска"""
            results = []
            
            for name, child in node.children.items():
                child_path = current_path + '/' + name if current_path != '/' else '/' + name
                
                # Проверяем совпадение имени
                if search_name in name:
                    results.append(child_path)
                
                # Рекурсивно ищем в поддиректориях
                if child.is_directory:
                    results.extend(search_recursive(child, child_path))
            
            return results
        
        return search_recursive(start_node, start_path)
    
    def get_directory_tree(self, start_path: str = ".") -> Optional[VFSNode]:
        """Возвращает узел дерева директорий для указанного пути"""
        return self._resolve_path(start_path)