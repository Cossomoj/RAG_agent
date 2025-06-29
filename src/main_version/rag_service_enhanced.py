"""
Enhanced RAG Service with Context7 Best Practices
- Metadata-enriched documents
- TimeWeightedVectorStoreRetriever support
- Improved markdown processing
- Better chunk strategy
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import faiss
import markdown

# Настройка путей
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# LangChain imports with enhanced features
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader
from langchain_community.vectorstores import FAISS
from langchain_community.docstore import InMemoryDocstore
from langchain.retrievers import TimeWeightedVectorStoreRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain.schema import Document as LCDocument
from langchain_gigachat import GigaChat
from langchain.chains import RetrievalQA

import websockets
import asyncio
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rag_enhanced.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedRAGService:
    """Улучшенный RAG сервис с Context7 best practices"""
    
    def __init__(self):
        logger.info("🚀 Инициализация Enhanced RAG Service...")
        
        # Пути к документам с улучшенной структурой
        self.docs_base_path = current_dir + "/docs"
        self.doc_packs = {
            "competency_lead": {
                "path": f"{self.docs_base_path}/Competency_Lead",
                "category": "leadership",
                "roles": ["лид", "lead", "руководитель"]
            },
            "intern": {
                "path": f"{self.docs_base_path}/Intern", 
                "category": "training",
                "roles": ["стажер", "intern", "начинающий"]
            },
            "specialist": {
                "path": f"{self.docs_base_path}/Specialist",
                "category": "technical", 
                "roles": ["специалист", "specialist", "разработчик"]
            },
            "po": {
                "path": f"{self.docs_base_path}/PO",
                "category": "management",
                "roles": ["po", "pm", "product", "manager"]
            },
            "full": {
                "path": f"{self.docs_base_path}/full",
                "category": "comprehensive",
                "roles": ["общий", "full", "все"]
            }
        }
        
        # Инициализация компонентов
        self.embeddings_model = None
        self.vector_stores = {}
        self.time_weighted_retrievers = {}
        self.llm = None
        
        # Загрузка и инициализация
        self._initialize_embeddings()
        self._load_enhanced_documents()
        self._create_enhanced_vector_stores()
        self._initialize_llm()
        
        logger.info("✅ Enhanced RAG Service инициализирован успешно!")

    def _initialize_embeddings(self):
        """Инициализация модели эмбеддингов"""
        logger.info("📊 Инициализация улучшенной модели эмбеддингов...")
        self.embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

    def _create_enhanced_documents(self, file_path: str, pack_key: str) -> List[Document]:
        """Создание документов с улучшенными метаданными"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Извлечение специализации из пути
            specialization = self._extract_specialization(file_path)
            
            # Улучшенная обработка markdown
            headers_to_split_on = [
                ("#", "Header 1"),
                ("##", "Header 2"), 
                ("###", "Header 3"),
            ]
            
            markdown_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=headers_to_split_on
            )
            
            # Сначала разбиваем по заголовкам
            md_header_splits = markdown_splitter.split_text(content)
            
            # Затем дополнительно по размеру
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=800,
                chunk_overlap=100,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            splits = text_splitter.split_documents(md_header_splits)
            
            # Обогащение метаданными
            enhanced_docs = []
            for i, split in enumerate(splits):
                # Базовые метаданные
                metadata = {
                    "source": file_path,
                    "filename": os.path.basename(file_path),
                    "pack": pack_key,
                    "category": self.doc_packs[pack_key]["category"],
                    "specialization": specialization,
                    "chunk_index": i,
                    "total_chunks": len(splits),
                    "created_at": datetime.now().isoformat(),
                    "file_size": len(content)
                }
                
                # Добавляем существующие метаданные
                metadata.update(split.metadata)
                
                # Анализ контента для дополнительных метаданных
                content_lower = split.page_content.lower()
                metadata["content_type"] = self._classify_content_type(content_lower)
                metadata["complexity_level"] = self._assess_complexity(split.page_content)
                metadata["keywords"] = self._extract_keywords(content_lower)
                
                enhanced_docs.append(Document(
                    page_content=split.page_content,
                    metadata=metadata
                ))
            
            return enhanced_docs
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания документов из {file_path}: {e}")
            return []

    def _extract_specialization(self, file_path: str) -> str:
        """Извлечение специализации из пути файла"""
        path_lower = file_path.lower()
        if "analyst" in path_lower or "аналитик" in path_lower:
            return "analyst"
        elif "java" in path_lower:
            return "java"
        elif "python" in path_lower:
            return "python" 
        elif "qa" in path_lower:
            return "qa"
        elif "web" in path_lower:
            return "web"
        elif "po" in path_lower or "pm" in path_lower:
            return "manager"
        return "general"

    def _classify_content_type(self, content: str) -> str:
        """Классификация типа контента"""
        if "матрица компетенций" in content or "competency matrix" in content:
            return "competency_matrix"
        elif "собеседование" in content or "interview" in content:
            return "interview_guide" 
        elif "практики" in content or "practices" in content:
            return "best_practices"
        elif "взаимодействие" in content or "interaction" in content:
            return "interaction_guide"
        elif "sdlc" in content or "жизненный цикл" in content:
            return "methodology"
        return "general_guide"

    def _assess_complexity(self, content: str) -> str:
        """Оценка сложности контента"""
        # Простая эвристика на основе длины и ключевых слов
        if len(content) < 200:
            return "basic"
        elif len(content) < 800:
            return "intermediate"
        else:
            return "advanced"

    def _extract_keywords(self, content: str) -> List[str]:
        """Извлечение ключевых слов"""
        keywords = []
        key_terms = [
            "компетенции", "навыки", "собеседование", "разработка", 
            "тестирование", "аналитика", "лидерство", "команда",
            "проект", "agile", "scrum", "качество", "процесс"
        ]
        
        for term in key_terms:
            if term in content:
                keywords.append(term)
        
        return keywords[:5]  # Ограничиваем количество

    def _load_enhanced_documents(self):
        """Загрузка документов с улучшенными возможностями"""
        logger.info("📚 Загрузка документов с улучшенными метаданными...")
        
        self.enhanced_docs = {}
        
        for pack_key, pack_info in self.doc_packs.items():
            pack_path = pack_info["path"]
            logger.info(f"📂 Обрабатываем пакет: {pack_key}")
            
            if not os.path.exists(pack_path):
                logger.warning(f"⚠️ Путь не найден: {pack_path}")
                continue
                
            pack_docs = []
            
            # Рекурсивная обработка .md файлов
            for root, dirs, files in os.walk(pack_path):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        docs = self._create_enhanced_documents(file_path, pack_key)
                        pack_docs.extend(docs)
            
            self.enhanced_docs[pack_key] = pack_docs
            logger.info(f"✅ {pack_key}: загружено {len(pack_docs)} чанков")

    def _create_enhanced_vector_stores(self):
        """Создание улучшенных векторных хранилищ с временным ранжированием"""
        logger.info("🏗️ Создание enhanced vector stores...")
        
        for pack_key, docs in self.enhanced_docs.items():
            if not docs:
                continue
                
            # Создаем стандартное FAISS хранилище
            vectorstore = FAISS.from_documents(
                documents=docs,
                embedding=self.embeddings_model
            )
            
            # Создаем TimeWeightedVectorStoreRetriever
            embedding_size = 384  # Размер эмбеддингов для paraphrase-multilingual-MiniLM-L12-v2
            index = faiss.IndexFlatL2(embedding_size)
            docstore = InMemoryDocstore({})
            
            faiss_store = FAISS(
                embedding_function=self.embeddings_model,
                index=index,
                docstore=docstore,
                index_to_docstore_id={}
            )
            
            # Добавляем документы во временно-взвешенное хранилище
            faiss_store.add_documents(docs)
            
            # Создаем временно-взвешенный retriever
            time_weighted_retriever = TimeWeightedVectorStoreRetriever(
                vectorstore=faiss_store,
                decay_rate=0.01,  # Медленное затухание важности по времени
                k=10
            )
            
            self.vector_stores[pack_key] = vectorstore
            self.time_weighted_retrievers[pack_key] = time_weighted_retriever
            
            logger.info(f"✅ Создано enhanced хранилище для {pack_key}: {len(docs)} документов")

    def _initialize_llm(self):
        """Инициализация LLM"""
        try:
            self.llm = GigaChat(
                credentials="здесь_должен_быть_ваш_токен",
                verify_ssl_certs=False,
                model="GigaChat",
                temperature=0.3,
                max_tokens=2000
            )
            logger.info("✅ GigaChat LLM инициализирован")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации LLM: {e}")
            self.llm = None

    def get_enhanced_retriever(self, user_id: int, role: str = "", spec: str = "", use_time_weighted: bool = True) -> object:
        """Получение улучшенного retriever с учетом контекста"""
        
        # Специальные ID используют полную базу
        if user_id in [777, 888, 999]:
            pack_key = "full"
        else:
            # Определение пакета по роли
            pack_key = self._determine_pack_by_role(role, spec)
        
        if use_time_weighted and pack_key in self.time_weighted_retrievers:
            logger.info(f"🔍 Используем TimeWeighted retriever для {pack_key}")
            return self.time_weighted_retrievers[pack_key]
        elif pack_key in self.vector_stores:
            logger.info(f"🔍 Используем стандартный retriever для {pack_key}")
            return self.vector_stores[pack_key].as_retriever(
                search_kwargs={"k": 10, "fetch_k": 20}
            )
        else:
            # Fallback на полную базу
            if use_time_weighted:
                return self.time_weighted_retrievers.get("full")
            return self.vector_stores.get("full", self.vector_stores[list(self.vector_stores.keys())[0]]).as_retriever()

    def _determine_pack_by_role(self, role: str, spec: str) -> str:
        """Определение пакета документов по роли"""
        role_lower = role.lower()
        spec_lower = spec.lower()
        
        # Проверяем каждый пакет
        for pack_key, pack_info in self.doc_packs.items():
            for role_keyword in pack_info["roles"]:
                if role_keyword in role_lower or role_keyword in spec_lower:
                    return pack_key
        
        return "full"  # По умолчанию

    def enhanced_search(self, query: str, user_id: int, role: str = "", spec: str = "", 
                       filters: Dict = None, use_reranking: bool = True) -> Dict:
        """Улучшенный поиск с фильтрацией и reranking"""
        
        retriever = self.get_enhanced_retriever(user_id, role, spec)
        
        try:
            # Базовый поиск
            docs = retriever.invoke(query)
            
            # Применяем фильтры метаданных если указаны
            if filters:
                docs = self._apply_metadata_filters(docs, filters)
            
            # Простой reranking по релевантности (можно улучшить)
            if use_reranking:
                docs = self._rerank_documents(docs, query)
            
            # Формируем ответ
            context = "\n\n".join([doc.page_content for doc in docs[:5]])
            
            if self.llm:
                response = self._generate_response(query, context)
            else:
                response = f"Контекст найден, но LLM недоступен:\n\n{context}"
                
            return {
                "response": response,
                "sources": [doc.metadata for doc in docs[:5]],
                "total_docs_found": len(docs)
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка enhanced поиска: {e}")
            return {"response": "Ошибка при поиске", "sources": [], "total_docs_found": 0}

    def _apply_metadata_filters(self, docs: List[Document], filters: Dict) -> List[Document]:
        """Применение фильтров по метаданным"""
        filtered_docs = []
        
        for doc in docs:
            include = True
            for key, value in filters.items():
                if key in doc.metadata:
                    if isinstance(value, list):
                        if doc.metadata[key] not in value:
                            include = False
                            break
                    else:
                        if doc.metadata[key] != value:
                            include = False
                            break
            
            if include:
                filtered_docs.append(doc)
        
        return filtered_docs

    def _rerank_documents(self, docs: List[Document], query: str) -> List[Document]:
        """Простое переранжирование документов"""
        # Простая эвристика - считаем количество совпадающих слов
        query_words = set(query.lower().split())
        
        scored_docs = []
        for doc in docs:
            content_words = set(doc.page_content.lower().split())
            score = len(query_words.intersection(content_words))
            
            # Бонус за метаданные
            if 'keywords' in doc.metadata:
                keyword_matches = len(set(doc.metadata['keywords']).intersection(query_words))
                score += keyword_matches * 2
                
            scored_docs.append((score, doc))
        
        # Сортируем по убыванию score
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        return [doc for score, doc in scored_docs]

    def _generate_response(self, query: str, context: str) -> str:
        """Генерация ответа с помощью LLM"""
        prompt = f"""
Контекст: {context}

Вопрос: {query}

Ответ на основе предоставленного контекста:
"""
        try:
            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            logger.error(f"❌ Ошибка генерации ответа: {e}")
            return "Ошибка при генерации ответа"

    def get_statistics(self) -> Dict:
        """Получение статистики enhanced системы"""
        stats = {
            "total_packs": len(self.doc_packs),
            "vector_stores": len(self.vector_stores),
            "time_weighted_retrievers": len(self.time_weighted_retrievers),
            "packs_detail": {}
        }
        
        for pack_key, docs in self.enhanced_docs.items():
            stats["packs_detail"][pack_key] = {
                "document_count": len(docs),
                "categories": list(set(doc.metadata.get("content_type", "unknown") for doc in docs)),
                "specializations": list(set(doc.metadata.get("specialization", "unknown") for doc in docs)),
                "complexity_levels": list(set(doc.metadata.get("complexity_level", "unknown") for doc in docs))
            }
        
        return stats

# Создание экземпляра enhanced сервиса
if __name__ == "__main__":
    enhanced_service = EnhancedRAGService()
    
    # Тестирование
    test_result = enhanced_service.enhanced_search(
        query="Как проводить собеседование с аналитиком?",
        user_id=1001,
        role="лид компетенции",
        spec="аналитик"
    )
    
    print("🎯 Тест enhanced поиска:")
    print(f"Ответ: {test_result['response'][:200]}...")
    print(f"Источников: {test_result['total_docs_found']}")
    
    # Статистика
    stats = enhanced_service.get_statistics()
    print(f"\n📊 Статистика enhanced системы:")
    print(f"Пакетов: {stats['total_packs']}")
    print(f"Vector stores: {stats['vector_stores']}")
    print(f"Time-weighted retrievers: {stats['time_weighted_retrievers']}") 