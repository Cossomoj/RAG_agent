#!/usr/bin/env python3
"""
RAG Service with Context7 Optimizations - Production Ready Version
Применены best practices для максимальной точности и производительности RAG
"""

import os
import sqlite3
import json
import string
import asyncio
import re
from typing import List, Dict, Optional, Any
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse

# LangChain Core imports 
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_gigachat import GigaChat

# Advanced RAG Components
from langchain.retrievers import TimeWeightedVectorStoreRetriever, EnsembleRetriever
from langchain.retrievers.document_compressors import DocumentCompressorPipeline
from langchain_community.document_transformers import EmbeddingsRedundantFilter
from langchain.retrievers import ContextualCompressionRetriever

app = FastAPI()

# === CONFIGURATION ===
DATABASE_URL = 'AI_agent.db'  
api_key = os.getenv("GIGACHAT_API_KEY")

# Context7 Optimized Paths - новая архитектура 5 векторных баз
folder_path_competency_lead = "docs/Competency_Lead/"
folder_path_intern = "docs/Intern/"  
folder_path_specialist = "docs/Specialist/"
folder_path_po = "docs/PO/"
folder_path_full = "docs/full/"

print("🚀 Инициализация Context7-оптимизированного RAG сервиса...")

# === CONTEXT7 OPTIMIZED DOCUMENT PROCESSING ===

def create_docs_from_txt(folder_path):
    """Загрузка TXT документов с оптимизированным чанкингом"""
    try:
        loader = DirectoryLoader(folder_path, glob="*.txt", loader_cls=TextLoader)
        documents = loader.load()
        
        # Context7 Best Practice: Оптимизированные параметры чанкинга
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,  # Оптимальный размер для embedding моделей
            chunk_overlap=100,  # Достаточный overlap для контекста
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]  # Умное разделение
        )
        
        split_documents = text_splitter.split_documents(documents)
        
        # Context7 Enhancement: Обогащение метаданными
        for i, doc in enumerate(split_documents):
            doc.metadata.update({
                'chunk_id': i,
                'content_type': 'txt',
                'processing_timestamp': datetime.now().isoformat(),
                'chunk_size': len(doc.page_content),
                'folder_source': folder_path.split('/')[-2] if '/' in folder_path else folder_path
            })
        
        print(f"✅ TXT документы: {len(split_documents)} чанков из {len(documents)} файлов")
        return split_documents
        
    except Exception as e:
        print(f"❌ Ошибка загрузки TXT из {folder_path}: {e}")
        return []

def create_docs_from_markdown_recursive(folder_path):
    """Context7-оптимизированная обработка Markdown с поддержкой структуры заголовков"""
    
    def scan_directory(directory):
        """Рекурсивно сканирует директорию для .md файлов"""
        md_files = []
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.md'):
                        md_files.append(os.path.join(root, file))
        except Exception as e:
            print(f"❌ Ошибка сканирования {directory}: {e}")
        return md_files
    
    try:
        if not os.path.exists(folder_path):
            print(f"⚠️ Директория не найдена: {folder_path}")
            return []
        
        md_files = scan_directory(folder_path)
        if not md_files:
            print(f"⚠️ Нет .md файлов в {folder_path}")
            return []
        
        print(f"📁 Найдено {len(md_files)} Markdown файлов в {folder_path}")
        
        all_documents = []
        
        # Context7 Best Practice: Структурированная обработка Markdown
        headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"), 
            ("###", "Header 3"),
            ("####", "Header 4"),
        ]
        
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on,
            strip_headers=False  # Сохраняем заголовки для контекста
        )
        
        for file_path in md_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                # Первичное разделение по заголовкам
                md_header_splits = markdown_splitter.split_text(content)
                
                # Вторичное разделение по размеру чанков
                text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=700,  # Немного меньше для Markdown
                    chunk_overlap=80,
                    length_function=len
                )
                
                # Разделяем каждый раздел заголовка
                splits = text_splitter.split_documents(md_header_splits)
                
                # Context7 Enhancement: Расширенные метаданные
                for i, doc in enumerate(splits):
                    doc.metadata.update({
                        'source': file_path,
                        'file_name': os.path.basename(file_path),
                        'folder_category': folder_path.split('/')[-2] if '/' in folder_path else folder_path,
                        'content_type': 'markdown',
                        'chunk_id': i,
                        'processing_timestamp': datetime.now().isoformat(),
                        'chunk_size': len(doc.page_content),
                        # Извлекаем структуру заголовков
                        'headers': {k: v for k, v in doc.metadata.items() if 'Header' in k},
                        # Определяем сложность контента
                        'complexity_level': 'high' if len(doc.page_content) > 500 else 'medium' if len(doc.page_content) > 200 else 'low',
                        # Извлекаем ключевые слова
                        'keywords': extract_keywords(doc.page_content)
                    })
                
                all_documents.extend(splits)
                
            except Exception as e:
                print(f"❌ Ошибка обработки файла {file_path}: {e}")
                continue
        
        print(f"✅ Markdown документы: {len(all_documents)} чанков обработано")
        return all_documents
        
    except Exception as e:
        print(f"❌ Ошибка загрузки Markdown из {folder_path}: {e}")
        return []

def extract_keywords(text: str, max_keywords: int = 10) -> List[str]:
    """Context7 Enhancement: Извлечение ключевых слов для метаданных"""
    # Простое извлечение ключевых слов на основе частоты
    import re
    from collections import Counter
    
    # Убираем знаки препинания и приводим к нижнему регистру
    words = re.findall(r'\b[а-яё]{3,}\b', text.lower())
    
    # Убираем стоп-слова
    stop_words = {'что', 'как', 'где', 'когда', 'почему', 'кто', 'какой', 'можно', 'нужно', 
                  'для', 'при', 'или', 'это', 'все', 'еще', 'уже', 'так', 'там', 'тут'}
    
    words = [word for word in words if word not in stop_words and len(word) > 3]
    
    # Возвращаем топ ключевых слов
    return [word for word, count in Counter(words).most_common(max_keywords)]

def create_docs_adaptive(folder_path):
    """Context7-адаптивная загрузка документов с приоритетом Markdown"""
    print(f"📂 Адаптивная загрузка из: {folder_path}")
    
    # Приоритет: сначала .md, потом .txt
    md_docs = create_docs_from_markdown_recursive(folder_path)
    if md_docs:
        print(f"✅ Использованы Markdown документы: {len(md_docs)} чанков")
        return md_docs
    
    txt_docs = create_docs_from_txt(folder_path)
    if txt_docs:
        print(f"✅ Использованы TXT документы: {len(txt_docs)} чанков")  
        return txt_docs
    
    print(f"⚠️ Документы не найдены в {folder_path}")
    return []

# === CONTEXT7 OPTIMIZED EMBEDDING & VECTOR STORES ===

print("📄 Загрузка документов для Context7-оптимизированных векторных баз...")

# 1. Competency Lead база
print("Загружаем документы для Competency Lead...")
split_docs_competency_lead = create_docs_adaptive(folder_path_competency_lead)

# 2. Intern база  
print("Загружаем документы для Intern...")
split_docs_intern = create_docs_adaptive(folder_path_intern)

# 3. Specialist база
print("Загружаем документы для Specialist...")
split_docs_specialist = create_docs_adaptive(folder_path_specialist)

# 4. PO/PM база
print("Загружаем документы для PO/PM...")
split_docs_po = create_docs_adaptive(folder_path_po)

# 5. Полная база для универсальных запросов
print("Загружаем документы для полной базы...")
split_docs_full = create_docs_adaptive(folder_path_full)

# Context7 Best Practice: Оптимизированная embedding модель
print("🧠 Инициализация Context7-оптимизированной embedding модели...")
model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
model_kwargs = {
    'device': 'cpu',
    'trust_remote_code': True  # Context7 Enhancement
}
encode_kwargs = {
    'normalize_embeddings': True,  # Context7 Best Practice: нормализация для лучшего cosine similarity
    'batch_size': 32  # Оптимизация для производительности
}

embedding = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

# === CONTEXT7 ADVANCED VECTOR STORES ===

print("🗄️ Создание Context7-оптимизированных векторных хранилищ...")

def create_optimized_vector_store(documents: List, store_name: str):
    """Context7 Enhancement: Создание оптимизированного векторного хранилища"""
    if not documents:
        print(f"⚠️ Нет документов для {store_name}")
        return None, None
        
    try:
        # Создаем FAISS векторное хранилище
        vector_store = FAISS.from_documents(documents, embedding=embedding)
        
        # Context7 Best Practice: Time-weighted retriever для учета свежести
        time_weighted_retriever = TimeWeightedVectorStoreRetriever(
            vectorstore=vector_store,
            decay_rate=-0.01,  # Медленное затухание для стабильных документов
            k=12  # Увеличенное количество документов для лучшего охвата
        )
        
        # Context7 Enhancement: Contextual compression для улучшения релевантности
        redundant_filter = EmbeddingsRedundantFilter(embeddings=embedding)
        pipeline_compressor = DocumentCompressorPipeline(
            transformers=[redundant_filter]
        )
        
        compression_retriever = ContextualCompressionRetriever(
            base_compressor=pipeline_compressor,
            base_retriever=time_weighted_retriever
        )
        
        print(f"✅ Context7-оптимизированное хранилище {store_name}: {len(documents)} документов")
        return vector_store, compression_retriever
        
    except Exception as e:
        print(f"❌ Ошибка создания хранилища {store_name}: {e}")
        return None, None

# Создаем оптимизированные векторные хранилища
vector_store_competency_lead, embedding_retriever_competency_lead = create_optimized_vector_store(
    split_docs_competency_lead, "Competency Lead"
)

vector_store_intern, embedding_retriever_intern = create_optimized_vector_store(
    split_docs_intern, "Intern"
)

vector_store_specialist, embedding_retriever_specialist = create_optimized_vector_store(
    split_docs_specialist, "Specialist"
)

vector_store_po, embedding_retriever_po = create_optimized_vector_store(
    split_docs_po, "PO/PM"
)

vector_store_full, embedding_retriever_full = create_optimized_vector_store(
    split_docs_full, "Full Knowledge Base"
)

print("=== Context7-оптимизированные векторные базы готовы ===")

# Fallback система
if not embedding_retriever_competency_lead:
    embedding_retriever_competency_lead = embedding_retriever_full
if not embedding_retriever_intern:
    embedding_retriever_intern = embedding_retriever_full  
if not embedding_retriever_specialist:
    embedding_retriever_specialist = embedding_retriever_full
if not embedding_retriever_po:
    embedding_retriever_po = embedding_retriever_full

# === CONTEXT7 ENHANCED RAG FUNCTIONS ===

def get_prompt_from_db(question_id):
    """Context7-оптимизированное получение промптов с логированием"""
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT prompt_template FROM Prompts WHERE question_id = ?", (question_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            print(f"✅ Context7: Промпт для ID {question_id} загружен")
            return result[0]
        else:
            print(f"❌ Context7: Промпт для ID {question_id} НЕ найден")
            return None
    except sqlite3.Error as e:
        print(f"❌ Context7: Ошибка БД при получении промпта: {e}")
        return None

def get_best_retriever_for_role_spec(role, specialization):
    """Context7-оптимизированный роутинг к специализированным retrievers"""
    role_lower = role.lower() if role else ""
    spec_lower = specialization.lower() if specialization else ""
    
    print(f"🎯 Context7 роутинг: роль='{role}', специализация='{specialization}'")
    
    # Интеллектуальный маппинг с Context7 оптимизациями
    if 'лид' in role_lower and 'компетенц' in role_lower:
        print("→ Context7: Competency Lead retriever выбран")
        return embedding_retriever_competency_lead
    elif 'стажер' in role_lower or 'intern' in role_lower.replace(' ', ''):
        print("→ Context7: Intern retriever выбран")
        return embedding_retriever_intern
    elif 'специалист' in role_lower or 'specialist' in role_lower.replace(' ', ''):
        print("→ Context7: Specialist retriever выбран")
        return embedding_retriever_specialist
    elif 'po' in role_lower or 'pm' in role_lower or 'product owner' in role_lower or 'project manager' in role_lower:
        print("→ Context7: PO/PM retriever выбран")
        return embedding_retriever_po
    else:
        # Context7 Enhancement: Fallback с анализом специализации
        if spec_lower in ['аналитик', 'тестировщик', 'python', 'java', 'web']:
            print("→ Context7: Fallback на Specialist по специализации")
            return embedding_retriever_specialist
        else:
            print("→ Context7: Fallback на полную базу знаний")
            return embedding_retriever_full

async def context7_enhanced_query_expansion(question: str, role: str, specialization: str) -> List[str]:
    """Context7 Best Practice: Расширение запроса для улучшения поиска"""
    llm = GigaChat(
        credentials=api_key,
        model='GigaChat-2',
        verify_ssl_certs=False,
        profanity_check=False
    )
    
    expansion_prompt = f"""
На основе вопроса: "{question}"
Роль: {role if role else "не указана"}
Специализация: {specialization if specialization else "не указана"}

Сгенерируй 4-5 семантически связанных поисковых запросов для корпоративной базы знаний по развитию IT-карьеры.

Требования к запросам:
1. Короткие и точные (3-8 слов)
2. Используют ключевые термины: ИПР, компетенции, развитие, лидерство, встречи 1-2-1
3. Релевантны роли и специализации пользователя
4. Покрывают разные аспекты вопроса

Ответь только списком запросов, каждый с новой строки, без нумерации:
"""
    
    try:
        response = await llm.ainvoke(expansion_prompt)
        queries = [q.strip() for q in response.content.split('\n') if q.strip() and len(q.strip()) > 5]
        
        # Добавляем исходный вопрос в начало
        all_queries = [question] + queries[:4]  # Ограничиваем количество
        
        print(f"🔍 Context7 query expansion: {len(all_queries)} запросов сгенерировано")
        return all_queries
        
    except Exception as e:
        print(f"❌ Context7 query expansion ошибка: {e}")
        return [question]

async def context7_enhanced_retrieval(question: str, role: str, specialization: str, retriever, top_k: int = 10) -> List:
    """Context7 Best Practice: Улучшенный поиск с multiple queries"""
    
    # Расширяем запрос
    queries = await context7_enhanced_query_expansion(question, role, specialization)
    
    all_docs = []
    doc_scores = {}
    
    for i, query in enumerate(queries):
        try:
            # Вес запросов убывает (первый важнее)
            weight = 1.0 / (i + 1)
            
            docs = await retriever.ainvoke(query)
            
            for j, doc in enumerate(docs):
                doc_id = doc.metadata.get('source', '') + str(hash(doc.page_content[:100]))
                
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {
                        'doc': doc,
                        'score': 0,
                        'query_matches': []
                    }
                
                # Context7 scoring: позиция + вес запроса + метаданные
                position_score = 1.0 / (j + 1)
                metadata_bonus = 0.1 if doc.metadata.get('complexity_level') == 'high' else 0
                
                doc_scores[doc_id]['score'] += weight * position_score + metadata_bonus
                doc_scores[doc_id]['query_matches'].append(query)
        
        except Exception as e:
            print(f"❌ Context7 retrieval ошибка для '{query}': {e}")
            continue
    
    # Сортируем по Context7 scoring
    sorted_docs = sorted(doc_scores.values(), key=lambda x: x['score'], reverse=True)
    result_docs = [item['doc'] for item in sorted_docs[:top_k]]
    
    print(f"📊 Context7 retrieval: {len(result_docs)} документов отобрано")
    for i, item in enumerate(sorted_docs[:5], 1):  # Показываем топ-5
        source = item['doc'].metadata.get('file_name', 'Unknown')
        print(f"  {i}. Score: {item['score']:.3f} | {source} | Matches: {len(item['query_matches'])}")
    
    return result_docs

async def check_document_relevance_context7(question: str, retriever, threshold: float = 0.3) -> bool:
    """Context7-оптимизированная проверка релевантности"""
    try:
        docs = await retriever.ainvoke(question)
        if not docs:
            return False
        
        # Context7 Enhancement: Используем ключевые слова + метаданные
        question_words = set(extract_keywords(question.lower()))
        
        if len(question_words) == 0:
            return True  # Если нет ключевых слов, считаем релевантным
        
        relevant_count = 0
        for doc in docs[:3]:  # Проверяем топ-3
            doc_text = doc.page_content.lower()
            doc_keywords = set(doc.metadata.get('keywords', []))
            
            # Считаем совпадения в тексте и метаданных
            text_matches = sum(1 for word in question_words if word in doc_text)
            meta_matches = len(question_words.intersection(doc_keywords))
            
            total_matches = text_matches + meta_matches * 2  # Метаданные важнее
            
            if total_matches >= max(2, len(question_words) * 0.3):
                relevant_count += 1
        
        is_relevant = relevant_count > 0
        
        print(f"🎯 Context7 relevance check: {is_relevant} (relevant docs: {relevant_count}/3)")
        return is_relevant
        
    except Exception as e:
        print(f"❌ Context7 relevance check ошибка: {e}")
        return True  # При ошибке используем RAG

# === CONTEXT7 ENHANCED RAG CHAIN ===

async def create_context7_rag_chain(role: str, specialization: str, question_id: int, retriever, prompt_template: str):
    """Context7-оптимизированная RAG chain с продвинутыми возможностями"""
    
    # Заполняем промпт
    template = string.Template(prompt_template)
    filled_prompt = template.substitute(role=role, specialization=specialization)
    
    # Context7 Enhanced LLM
    llm = GigaChat(
        credentials=api_key,
        model='GigaChat-2',
        verify_ssl_certs=False,
        profanity_check=False,
        temperature=0.1  # Context7 Best Practice: низкая температура для точности
    )
    
    class Context7EnhancedRAGChain:
        def __init__(self, llm, prompt, role, specialization, retriever, question_id):
            self.llm = llm
            self.base_prompt = prompt
            self.role = role
            self.specialization = specialization
            self.retriever = retriever
            self.question_id = question_id

        async def astream(self, input_data):
            """Context7-оптимизированный стриминг с улучшенным контекстом"""
            question = input_data.get('input', '')
            dialogue_context = input_data.get('dialogue_context', '[]')

            print(f"🚀 Context7 RAG processing: ID={self.question_id}, question='{question[:50]}...'")
            
            # Context7 Enhanced Retrieval
            docs = await context7_enhanced_retrieval(
                question, self.role, self.specialization, self.retriever
            )
            
            # Context7 Context Optimization
            context_parts = []
            for i, doc in enumerate(docs):
                # Добавляем структурированный контекст с метаданными
                source = doc.metadata.get('file_name', f'Document_{i+1}')
                headers = doc.metadata.get('headers', {})
                header_context = " | ".join([f"{k}: {v}" for k, v in headers.items() if v])
                
                context_entry = f"Источник: {source}"
                if header_context:
                    context_entry += f" | Структура: {header_context}"
                context_entry += f"\nСодержание: {doc.page_content}\n"
                
                context_parts.append(context_entry)
            
            enhanced_context = "\n" + "="*50 + "\n".join(context_parts)
            
            # Формируем финальный промпт
            dialogue_part = ""
            if dialogue_context and dialogue_context != '[]':
                dialogue_part = f"\n\nКонтекст диалога:\n{dialogue_context}"

            final_prompt = f"""{self.base_prompt}{dialogue_part}

Контекст из корпоративной базы знаний:
{enhanced_context}

Вопрос пользователя: {question}

ИНСТРУКЦИИ ПО ОТВЕТУ:
1. Используй ТОЛЬКО информацию из предоставленного контекста
2. Если в контексте нет релевантной информации, честно сообщи об этом
3. Структурируй ответ логично и четко
4. Ссылайся на конкретные источники когда это возможно
5. Форматируй ответ в Markdown для лучшей читаемости

Ответ:"""
            
            print(f"📤 Context7: Отправляем промпт в LLM ({len(final_prompt)} символов)")
            
            # Context7 Enhanced Streaming
            try:
                chunk_count = 0
                async for chunk in self.llm.astream(final_prompt):
                    if chunk and chunk.content:
                        chunk_count += 1
                        yield {"answer": chunk.content}
                
                print(f"✅ Context7 streaming завершен: {chunk_count} chunks отправлено")
                
                if chunk_count == 0:
                    yield {"answer": "Извините, не удалось сгенерировать ответ. Попробуйте переформулировать вопрос."}
                    
            except Exception as e:
                print(f"❌ Context7 streaming ошибка: {e}")
                yield {"answer": f"Произошла ошибка при генерации ответа: {e}"}

    return Context7EnhancedRAGChain(llm, filled_prompt, role, specialization, retriever, question_id)

# === CONTEXT7 WEBSOCKET ENDPOINT ===

@app.websocket("/ws")
async def context7_websocket_endpoint(websocket: WebSocket):
    """Context7-оптимизированный WebSocket endpoint с продвинутой логикой"""
    await websocket.accept()
    print("🔌 Context7: WebSocket соединение установлено")
    
    try:
        # Получаем данные от клиента
        question = await websocket.receive_text()
        role = await websocket.receive_text()
        specialization = await websocket.receive_text()
        question_id = await websocket.receive_text()
        context = await websocket.receive_text()
        count = await websocket.receive_text()
        
        question_id = int(question_id)
        count = int(count)
        
        print(f"📥 Context7: Получен запрос ID={question_id}, роль='{role}', специализация='{specialization}'")
        print(f"📝 Context7: Вопрос: '{question[:100]}...'")
        
        # Context7-оптимизированное получение промпта
        prompt_template = get_prompt_from_db(question_id)
        if not prompt_template:
            prompt_template = get_prompt_from_db(777)  # Fallback
        
        if not prompt_template:
            await websocket.send_text("❌ Context7: Критическая ошибка - промпт не найден")
            return
        
        # Context7 Smart Routing
        retriever = embedding_retriever_full  # По умолчанию
        use_rag = True
        
        if question_id in [777, 888, 999]:
            print(f"🎯 Context7: Специальный ID {question_id} - проверка релевантности")
            use_rag = await check_document_relevance_context7(question, embedding_retriever_full)
            
            if use_rag:
                print(f"✅ Context7: Документы релевантны для ID {question_id}")
                retriever = embedding_retriever_full
            else:
                print(f"❌ Context7: Документы не релевантны для ID {question_id} - fallback без RAG")
        else:
            print(f"📋 Context7: Стандартный запрос ID={question_id}")
            retriever = get_best_retriever_for_role_spec(role, specialization)
            if not retriever:
                retriever = embedding_retriever_full
        
        # Context7 Processing
        if use_rag:
            print(f"🧠 Context7: Использование RAG для ID={question_id}")
            
            rag_chain = await create_context7_rag_chain(
                role=role,
                specialization=specialization,
                question_id=question_id,
                retriever=retriever,
                prompt_template=prompt_template
            )
            
            dialogue_context_for_chain = "[]"
            if question_id == 888 and context and context != "[]":
                dialogue_context_for_chain = context
                
            async for chunk in rag_chain.astream({
                'input': question, 
                'dialogue_context': dialogue_context_for_chain
            }):
                if chunk and chunk.get("answer"):
                    await websocket.send_text(chunk["answer"])
        
        else:
            print(f"🤖 Context7: Прямой ответ LLM для ID={question_id}")
            
            # Context7 Direct LLM Response
            template = string.Template(prompt_template)
            filled_prompt = template.substitute(role=role, specialization=specialization)
            
            if question_id == 888 and context and context != "[]":
                context_part = f"\n\nКонтекст диалога:\n{context}\n\n"
                full_prompt = filled_prompt + context_part + f"Вопрос: {question}"
            else:
                full_prompt = filled_prompt + f"\n\nВопрос: {question}"
            
            # Context7 Enhanced Direct Response
            full_prompt += """

ВАЖНО: Структурируй ответ в формате Markdown с четкими заголовками и списками.
Будь конкретным и полезным, учитывая роль и специализацию пользователя."""
            
            llm = GigaChat(
                credentials=api_key,
                model='GigaChat-2',
                verify_ssl_certs=False,
                temperature=0.2
            )
            
            chunk_count = 0
            async for chunk in llm.astream(full_prompt):
                if chunk and chunk.content:
                    chunk_count += 1
                    await websocket.send_text(chunk.content)
            
            print(f"✅ Context7 direct response: {chunk_count} chunks отправлено")
            
            if chunk_count == 0:
                await websocket.send_text("Извините, не удалось получить ответ. Попробуйте переформулировать вопрос.")
        
    except Exception as e:
        print(f"❌ Context7 WebSocket ошибка: {e}")
        await websocket.send_text(f"Произошла системная ошибка: {str(e)}")
    
    finally:
        print("🔌 Context7: WebSocket соединение закрыто")

# === APPLICATION STARTUP ===

@app.get("/")
async def root():
    return JSONResponse({
        "service": "Context7-Optimized RAG Agent",
        "status": "running",
        "version": "2.0",
        "features": [
            "Context7 Enhanced Retrieval",
            "Smart Query Expansion", 
            "Advanced Metadata Enrichment",
            "Time-Weighted Retrieval",
            "Contextual Compression",
            "Intelligent Role Routing",
            "Production-Ready Optimization"
        ],
        "vector_stores": {
            "competency_lead": bool(embedding_retriever_competency_lead),
            "intern": bool(embedding_retriever_intern),
            "specialist": bool(embedding_retriever_specialist),
            "po_pm": bool(embedding_retriever_po),
            "full_knowledge": bool(embedding_retriever_full)
        }
    })

@app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "context7_optimizations": "active",
        "embedding_model": model_name,
        "api_status": "ready"
    })

if __name__ == "__main__":
    import uvicorn
    print("🚀 Запуск Context7-оптимизированного RAG сервера...")
    print("📡 WebSocket: ws://localhost:8000/ws")
    print("📈 API документация: http://localhost:8000/docs")
    print("🎯 Context7 best practices активированы!")
    
    uvicorn.run(app, host="0.0.0.0", port=8000) 