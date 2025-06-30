import os
from typing import Dict, List

class RAGDocumentManager:
    def __init__(self, base_path: str = 'src/main_version/docs'):
        self.base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', base_path))
        self.packs = {
            "pack_1": os.path.join(self.base_path, "docs_pack_1"),
            "pack_2": os.path.join(self.base_path, "docs_pack_2"),
            "pack_3": os.path.join(self.base_path, "docs_pack_3"),
            "pack_full": os.path.join(self.base_path, "docs_pack_full")
        }
        # Создаем директории, если они не существуют
        for pack_path in self.packs.values():
            os.makedirs(pack_path, exist_ok=True)

    def get_all_documents(self) -> Dict[str, List[Dict]]:
        """Получение списка всех документов по всем пакетам"""
        documents = {}
        for pack_name, pack_path in self.packs.items():
            if pack_name != "pack_full":  # Пропускаем pack_full, так как он содержит копии
                documents[pack_name] = []
                if os.path.exists(pack_path):
                    for filename in os.listdir(pack_path):
                        if filename.endswith('.txt'):
                            file_path = os.path.join(pack_path, filename)
                            file_stat = os.stat(file_path)
                            documents[pack_name].append({
                                'filename': filename,
                                'size': file_stat.st_size,
                                'modified': file_stat.st_mtime,
                                'pack': pack_name
                            })
        return documents

    def add_document(self, content: str, filename: str, pack_name: str) -> None:
        """Добавление нового документа"""
        if pack_name not in self.packs or pack_name == "pack_full":
            raise ValueError(f"Неверное имя пакета: {pack_name}")

        if not filename.endswith('.txt'):
            filename = f"{filename}.txt"

        # Сохраняем в указанный пакет
        file_path = os.path.join(self.packs[pack_name], filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Также сохраняем в pack_full
        full_path = os.path.join(self.packs["pack_full"], filename)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def delete_document(self, filename: str, pack_name: str) -> None:
        """Удаление документа"""
        if pack_name not in self.packs or pack_name == "pack_full":
            raise ValueError(f"Неверное имя пакета: {pack_name}")

        # Удаляем из указанного пакета
        file_path = os.path.join(self.packs[pack_name], filename)
        if os.path.exists(file_path):
            os.remove(file_path)

        # Также удаляем из pack_full
        full_path = os.path.join(self.packs["pack_full"], filename)
        if os.path.exists(full_path):
            os.remove(full_path)

    def get_document_content(self, filename: str, pack_name: str) -> str:
        """Получение содержимого документа"""
        if pack_name not in self.packs:
            raise ValueError(f"Неверное имя пакета: {pack_name}")

        file_path = os.path.join(self.packs[pack_name], filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {filename}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def update_document(self, content: str, filename: str, pack_name: str) -> None:
        """Обновление содержимого документа"""
        self.delete_document(filename, pack_name)
        self.add_document(content, filename, pack_name) 
