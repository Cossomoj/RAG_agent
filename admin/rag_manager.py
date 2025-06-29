import os
from typing import Dict, List
import markdown
from pathlib import Path

class RAGDocumentManager:
    def __init__(self, base_path: str = 'src/main_version/docs'):
        """
        Инициализирует менеджер документов RAG для новой архитектуры с .md файлами
        """
        self.base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', base_path))
        
        # Новая структура пакетов документов
        self.packs = {
            "competency_lead": {
                "name": "Competency Lead",
                "description": "Документы для лидов компетенций",
                "path": os.path.join(self.base_path, "Competency_Lead")
            },
            "intern": {
                "name": "Intern",
                "description": "Документы для стажеров", 
                "path": os.path.join(self.base_path, "Intern")
            },
            "specialist": {
                "name": "Specialist",
                "description": "Документы для специалистов",
                "path": os.path.join(self.base_path, "Specialist")
            },
            "po": {
                "name": "Product Owner / Project Manager",
                "description": "Документы для PO/PM",
                "path": os.path.join(self.base_path, "PO")
            },
            "full": {
                "name": "Full Database",
                "description": "Полная база документов (для свободных вопросов)",
                "path": os.path.join(self.base_path, "full")
            }
        }
        
        # Создаем директории, если они не существуют
        for pack_info in self.packs.values():
            os.makedirs(pack_info["path"], exist_ok=True)

    def get_all_documents(self) -> Dict[str, List[Dict]]:
        """Получение списка всех документов по всем пакетам (рекурсивно для .md файлов)"""
        documents = {}
        
        for pack_key, pack_info in self.packs.items():
            pack_path = pack_info["path"]
            documents[pack_key] = {
                "name": pack_info["name"],
                "description": pack_info["description"],
                "files": []
            }
            
            if os.path.exists(pack_path):
                # Рекурсивно собираем все .md файлы
                for root, dirs, files in os.walk(pack_path):
                    for file in files:
                        if file.endswith('.md'):
                            file_path = os.path.join(root, file)
                            relative_path = os.path.relpath(file_path, pack_path)
                            file_stat = os.stat(file_path)
                            
                            documents[pack_key]["files"].append({
                                'filename': file,
                                'relative_path': relative_path,
                                'full_path': file_path,
                                'size': file_stat.st_size,
                                'modified': file_stat.st_mtime,
                                'pack': pack_key,
                                'folder': os.path.dirname(relative_path) if os.path.dirname(relative_path) else "/"
                            })
        
        return documents

    def add_document(self, content: str, filename: str, pack_name: str, subfolder: str = "") -> None:
        """Добавление нового документа"""
        if pack_name not in self.packs:
            raise ValueError(f"Неверное имя пакета: {pack_name}")

        # Убеждаемся, что файл имеет расширение .md
        if not filename.endswith('.md'):
            filename = f"{filename}.md"

        # Определяем полный путь с учетом подпапки
        pack_path = self.packs[pack_name]["path"]
        if subfolder:
            target_dir = os.path.join(pack_path, subfolder)
        else:
            target_dir = pack_path
        
        # Создаем директории если не существуют
        os.makedirs(target_dir, exist_ok=True)
        
        # Сохраняем в указанный пакет
        file_path = os.path.join(target_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Также сохраняем в полную базу (только имя файла без структуры папок)
        if pack_name != "full":
            full_path = os.path.join(self.packs["full"]["path"], filename)
            os.makedirs(self.packs["full"]["path"], exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

    def delete_document(self, relative_path: str, pack_name: str) -> None:
        """Удаление документа"""
        if pack_name not in self.packs:
            raise ValueError(f"Неверное имя пакета: {pack_name}")

        # Удаляем из указанного пакета
        pack_path = self.packs[pack_name]["path"]
        file_path = os.path.join(pack_path, relative_path)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Удален файл: {file_path}")

        # Также удаляем из полной базы (только имя файла)
        if pack_name != "full":
            filename = os.path.basename(relative_path)
            full_path = os.path.join(self.packs["full"]["path"], filename)
            if os.path.exists(full_path):
                os.remove(full_path)
                print(f"Удален файл из полной базы: {full_path}")

    def get_document_content(self, relative_path: str, pack_name: str) -> str:
        """Получение содержимого документа"""
        if pack_name not in self.packs:
            raise ValueError(f"Неверное имя пакета: {pack_name}")

        pack_path = self.packs[pack_name]["path"]
        file_path = os.path.join(pack_path, relative_path)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {relative_path} в пакете {pack_name}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def update_document(self, content: str, relative_path: str, pack_name: str) -> None:
        """Обновление содержимого документа"""
        if pack_name not in self.packs:
            raise ValueError(f"Неверное имя пакета: {pack_name}")

        pack_path = self.packs[pack_name]["path"]
        file_path = os.path.join(pack_path, relative_path)
        
        # Создаем директории если не существуют
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Обновляем файл
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Также обновляем в полной базе (только имя файла)
        if pack_name != "full":
            filename = os.path.basename(relative_path)
            full_path = os.path.join(self.packs["full"]["path"], filename)
            os.makedirs(self.packs["full"]["path"], exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

    def get_document_as_html(self, relative_path: str, pack_name: str) -> str:
        """Получение содержимого документа в формате HTML для предварительного просмотра"""
        content = self.get_document_content(relative_path, pack_name)
        
        # Конвертируем Markdown в HTML
        md = markdown.Markdown(extensions=['tables', 'fenced_code', 'toc'])
        html_content = md.convert(content)
        
        return html_content

    def search_documents(self, query: str, pack_name: str = None) -> List[Dict]:
        """Поиск документов по содержимому"""
        results = []
        query_lower = query.lower()
        
        packs_to_search = [pack_name] if pack_name else list(self.packs.keys())
        
        for pack_key in packs_to_search:
            if pack_key not in self.packs:
                continue
                
            pack_path = self.packs[pack_key]["path"]
            if not os.path.exists(pack_path):
                continue
                
            for root, dirs, files in os.walk(pack_path):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, pack_path)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                
                            if query_lower in content.lower():
                                # Находим контекст вокруг найденного текста
                                lines = content.split('\n')
                                matching_lines = []
                                for i, line in enumerate(lines):
                                    if query_lower in line.lower():
                                        start = max(0, i-2)
                                        end = min(len(lines), i+3)
                                        context = '\n'.join(lines[start:end])
                                        matching_lines.append({
                                            'line_number': i+1,
                                            'context': context
                                        })
                                
                                results.append({
                                    'filename': file,
                                    'relative_path': relative_path,
                                    'pack': pack_key,
                                    'pack_name': self.packs[pack_key]["name"],
                                    'matches': matching_lines
                                })
                        except Exception as e:
                            print(f"Ошибка при поиске в файле {file_path}: {e}")
        
        return results

    def get_pack_statistics(self) -> Dict:
        """Получение статистики по пакетам документов"""
        stats = {}
        
        for pack_key, pack_info in self.packs.items():
            pack_path = pack_info["path"]
            stats[pack_key] = {
                "name": pack_info["name"],
                "description": pack_info["description"],
                "total_files": 0,
                "total_size": 0,
                "subfolders": set()
            }
            
            if os.path.exists(pack_path):
                for root, dirs, files in os.walk(pack_path):
                    md_files = [f for f in files if f.endswith('.md')]
                    stats[pack_key]["total_files"] += len(md_files)
                    
                    # Добавляем подпапки
                    rel_root = os.path.relpath(root, pack_path)
                    if rel_root != ".":
                        stats[pack_key]["subfolders"].add(rel_root)
                    
                    # Считаем размер файлов
                    for file in md_files:
                        file_path = os.path.join(root, file)
                        stats[pack_key]["total_size"] += os.path.getsize(file_path)
                
                stats[pack_key]["subfolders"] = list(stats[pack_key]["subfolders"])
        
        return stats 