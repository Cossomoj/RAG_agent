#!/usr/bin/env python3
"""
RAG Service - Новая версия с Context7 оптимизациями
Совместима с простой системой запуска (без config.yaml)
Применены best practices для максимальной точности RAG
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

import uvicorn

app = FastAPI()

# === ПРОСТАЯ КОНФИГУРАЦИЯ БЕЗ CONFIG.YAML ===
DATABASE_URL = "AI_agent.db"  # Локальный путь
api_key = os.getenv("GIGACHAT_API_KEY")

# Context7 Optimized Paths - используем существующую структуру docs/
folder_path_competency_lead = os.path.join(os.path.dirname(__file__), "docs/Competency_Lead/")
folder_path_intern = os.path.join(os.path.dirname(__file__), "docs/Intern/")
folder_path_specialist = os.path.join(os.path.dirname(__file__), "docs/Specialist/")
folder_path_po = os.path.join(os.path.dirname(__file__), "docs/PO/")
folder_path_full = os.path.join(os.path.dirname(__file__), "docs/full/")

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
    
    # Сначала пробуем загрузить Markdown файлы
    md_docs = create_docs_from_markdown_recursive(folder_path)
    
    # Если нет Markdown, загружаем TXT
    if not md_docs:
        txt_docs = create_docs_from_txt(folder_path)
        return txt_docs
    
    return md_docs

# === ИНИЦИАЛИЗАЦИЯ EMBEDDING МОДЕЛИ ===
print("🔧 Инициализация embedding модели...")
model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': False}
embedding = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

# === CONTEXT7 OPTIMIZED VECTOR STORES ===

def create_optimized_vector_store(documents: List, store_name: str):
    """Context7-оптимизированное создание векторного хранилища"""
    if not documents:
        print(f"⚠️ Нет документов для создания векторного хранилища {store_name}")
        return None
    
    try:
        print(f"🔧 Создание оптимизированного векторного хранилища {store_name}...")
        
        # Context7 Best Practice: Оптимизированные параметры для FAISS
        vector_store = FAISS.from_documents(
            documents, 
            embedding=embedding,
            normalize_L2=True  # Нормализация для лучшего similarity search
        )
        
        print(f"✅ Векторное хранилище {store_name}: {len(documents)} документов")
        return vector_store
        
    except Exception as e:
        print(f"❌ Ошибка создания векторного хранилища {store_name}: {e}")
        return None

# Загрузка и создание векторных хранилищ
print("📚 Загрузка документов и создание векторных хранилищ...")

competency_lead_docs = create_docs_adaptive(folder_path_competency_lead)
intern_docs = create_docs_adaptive(folder_path_intern)
specialist_docs = create_docs_adaptive(folder_path_specialist)
po_docs = create_docs_adaptive(folder_path_po)
full_docs = create_docs_adaptive(folder_path_full)

# Создание оптимизированных векторных хранилищ
vector_store_competency_lead = create_optimized_vector_store(competency_lead_docs, "Competency_Lead")
vector_store_intern = create_optimized_vector_store(intern_docs, "Intern")
vector_store_specialist = create_optimized_vector_store(specialist_docs, "Specialist")
vector_store_po = create_optimized_vector_store(po_docs, "PO")
vector_store_full = create_optimized_vector_store(full_docs, "Full")

# Создание retrievers с оптимизированными параметрами
embedding_retriever_competency_lead = vector_store_competency_lead.as_retriever(search_kwargs={"k": 12}) if vector_store_competency_lead else None
embedding_retriever_intern = vector_store_intern.as_retriever(search_kwargs={"k": 12}) if vector_store_intern else None
embedding_retriever_specialist = vector_store_specialist.as_retriever(search_kwargs={"k": 12}) if vector_store_specialist else None
embedding_retriever_po = vector_store_po.as_retriever(search_kwargs={"k": 12}) if vector_store_po else None
embedding_retriever_full = vector_store_full.as_retriever(search_kwargs={"k": 15}) if vector_store_full else None

print("✅ Все векторные хранилища созданы!")

# === DATABASE FUNCTIONS ===

def get_prompt_from_db(question_id):
    """Получает промт из базы данных по ID вопроса (ИСПРАВЛЕНО!)"""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        # ИСПРАВЛЕНИЕ: Используем правильное поле question_id вместо id
        cursor.execute("SELECT prompt_template FROM Prompts WHERE question_id = ?", (question_id,))
        result = cursor.fetchone()
        if result:
            # ИСПРАВЛЕНИЕ: Убираем экранированные символы \\n
            prompt_template = result[0].replace('\\n', '\n')
            return prompt_template
        else:
            return None
    finally:
        conn.close()

# === CONTEXT7 ENHANCED RETRIEVER SELECTION ===

def get_best_retriever_for_role_spec(role, specialization):
    """Context7-оптимизированный выбор retriever на основе роли и специализации"""
    role_lower = role.lower() if role else ""
    spec_lower = specialization.lower() if specialization else ""
    
    print(f"🎯 Выбор retriever для роли: '{role}', специализации: '{specialization}'")
    
    # Context7 Enhanced Mapping
    if 'лид' in role_lower or 'lead' in role_lower:
        print("📋 Выбран Competency_Lead retriever")
        return embedding_retriever_competency_lead or embedding_retriever_full
    elif 'стажер' in role_lower or 'intern' in role_lower:
        print("🎓 Выбран Intern retriever")
        return embedding_retriever_intern or embedding_retriever_full
    elif 'специалист' in role_lower or 'specialist' in role_lower:
        print("💼 Выбран Specialist retriever")
        return embedding_retriever_specialist or embedding_retriever_full
    elif 'po' in role_lower or 'pm' in role_lower or 'продакт' in role_lower:
        print("🎯 Выбран PO retriever")
        return embedding_retriever_po or embedding_retriever_full
    else:
        print("📚 Выбран Full retriever (fallback)")
        return embedding_retriever_full

# === CONTEXT7 ENHANCED QUERY PROCESSING ===

async def context7_enhanced_query_expansion(question: str, role: str, specialization: str) -> List[str]:
    """Context7 Enhanced: Расширение запроса для улучшения поиска"""
    
    llm = GigaChat(
        credentials=api_key,
        model='GigaChat-2',
        verify_ssl_certs=False,
        profanity_check=False
    )
    
    expansion_prompt = f"""
Дан вопрос: "{question}"
Роль: {role if role else "не указана"}
Специализация: {specialization if specialization else "не указана"}

Создай 4-5 альтернативных поисковых запросов для корпоративной базы знаний по развитию карьеры в IT:

Фокус на термины: "ИПР", "индивидуальный план развития", "лид компетенции", "встречи 1-2-1", "цели развития", "компетенции", "обратная связь", "мониторинг прогресса", "карьерная лестница"

Ответь только списком запросов без нумерации:
"""
    
    try:
        response = await llm.ainvoke(expansion_prompt)
        expanded_queries = [q.strip() for q in response.content.split('\n') if q.strip() and not q.strip().startswith('-')]
        return [question] + expanded_queries[:4]  # Оригинальный + 4 расширенных
    except Exception as e:
        print(f"⚠️ Ошибка расширения запроса: {e}")
        return [question]

async def context7_enhanced_retrieval(question: str, role: str, specialization: str, retriever, top_k: int = 10) -> List:
    """Context7 Enhanced: Улучшенный поиск с расширением запроса"""
    
    # Расширяем запрос
    expanded_queries = await context7_enhanced_query_expansion(question, role, specialization)
    
    all_docs = []
    seen_content = set()
    
    for query in expanded_queries:
        try:
            docs = retriever.get_relevant_documents(query)
            
            # Дедуплицируем документы
            for doc in docs:
                content_hash = hash(doc.page_content[:200])  # Используем первые 200 символов как хеш
                if content_hash not in seen_content:
                    seen_content.add(content_hash)
                    all_docs.append(doc)
                    
        except Exception as e:
            print(f"⚠️ Ошибка поиска для запроса '{query}': {e}")
            continue
    
    # Возвращаем топ документов
    return all_docs[:top_k]

async def check_document_relevance_context7(question: str, retriever, threshold: float = 0.3) -> bool:
    """Context7: Проверка релевантности документов"""
    try:
        docs = retriever.get_relevant_documents(question)
        if not docs:
            return False
        
        # Простая проверка релевантности через ключевые слова
        question_keywords = set(re.findall(r'\b[а-яё]{3,}\b', question.lower()))
        
        for doc in docs[:3]:  # Проверяем топ-3 документа
            doc_keywords = set(re.findall(r'\b[а-яё]{3,}\b', doc.page_content.lower()))
            overlap = len(question_keywords.intersection(doc_keywords))
            
            if overlap >= 2:  # Минимум 2 общих ключевых слова
                return True
        
        return False
        
    except Exception as e:
        print(f"⚠️ Ошибка проверки релевантности: {e}")
        return True  # Возвращаем True в случае ошибки

# === CONTEXT7 ENHANCED RAG CHAIN ===

async def create_context7_rag_chain(role: str, specialization: str, question_id: int, retriever, prompt_template: str):
    """Context7-оптимизированная RAG цепочка"""
    
    # Заполнение промпта
    template = string.Template(prompt_template)
    filled_prompt = template.substitute(role=role, specialization=specialization)
    
    prompt = ChatPromptTemplate.from_template(filled_prompt)
    
    llm = GigaChat(
        credentials=api_key,
        model='GigaChat-2',
        verify_ssl_certs=False,
        profanity_check=False
    )
    
    class Context7EnhancedRAGChain:
        def __init__(self, llm, prompt, role, specialization, retriever, question_id):
            self.llm = llm
            self.prompt = prompt
            self.role = role
            self.specialization = specialization
            self.retriever = retriever
            self.question_id = question_id
        
        async def astream(self, input_data):
            question = input_data.get("input", "")
            
            # Context7 Enhanced Retrieval
            context_docs = await context7_enhanced_retrieval(
                question, self.role, self.specialization, self.retriever, top_k=12
            )
            
            # Формируем контекст
            context = "\n\n".join([doc.page_content for doc in context_docs])
            
            # Создаем финальный промпт
            messages = self.prompt.format_messages(context=context, input=question)
            
            # Стримим ответ
            async for chunk in self.llm.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
    
    return Context7EnhancedRAGChain(llm, prompt, role, specialization, retriever, question_id)

# === WEBSOCKET ENDPOINT ===

@app.websocket("/ws")
async def context7_websocket_endpoint(websocket: WebSocket):
    """Context7-оптимизированный WebSocket endpoint"""
    await websocket.accept()
    print("🔌 WebSocket соединение установлено")
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Извлекаем данные
            user_id = message_data.get("user_id")
            question = message_data.get("question", "")
            role = message_data.get("role", "")
            specialization = message_data.get("specialization", "")
            question_id = message_data.get("question_id")
            
            print(f"📨 Получен запрос: user_id={user_id}, question_id={question_id}")
            print(f"🎭 Роль: {role}, Специализация: {specialization}")
            print(f"❓ Вопрос: {question}")
            
            # Проверяем обязательные поля
            if not question or not question_id:
                await websocket.send_text(json.dumps({
                    "error": "Отсутствуют обязательные поля: question или question_id"
                }))
                continue
            
            # Получаем промпт из базы данных
            prompt_template = get_prompt_from_db(question_id)
            if not prompt_template:
                await websocket.send_text(json.dumps({
                    "error": f"Промпт не найден для question_id: {question_id}"
                }))
                continue
            
            # Context7: Выбираем лучший retriever
            retriever = get_best_retriever_for_role_spec(role, specialization)
            if not retriever:
                await websocket.send_text(json.dumps({
                    "error": "Retriever недоступен"
                }))
                continue
            
            # Context7: Проверяем релевантность (только для специфических ID)
            if question_id not in [777, 888, 999]:
                is_relevant = await check_document_relevance_context7(question, retriever)
                if not is_relevant:
                    await websocket.send_text(json.dumps({
                        "error": "Извините, в базе знаний нет релевантной информации по вашему вопросу."
                    }))
                    continue
            
            try:
                # Создаем Context7-оптимизированную RAG цепочку
                rag_chain = await create_context7_rag_chain(
                    role, specialization, question_id, retriever, prompt_template
                )
                
                # Начинаем потоковую генерацию
                await websocket.send_text(json.dumps({"stream_start": True}))
                
                full_answer = ""
                async for chunk in rag_chain.astream({"input": question}):
                    if chunk:
                        full_answer += chunk
                        await websocket.send_text(json.dumps({"chunk": chunk}))
                
                # Сохраняем в базу данных
                if user_id and full_answer.strip():
                    save_message_to_db(user_id, question, full_answer.strip(), role, specialization)
                
                # Сигнализируем окончание стриминга
                await websocket.send_text(json.dumps({"stream_end": True}))
                print("✅ Ответ успешно отправлен")
                
            except Exception as e:
                print(f"❌ Ошибка генерации ответа: {e}")
                await websocket.send_text(json.dumps({
                    "error": f"Ошибка генерации ответа: {str(e)}"
                }))
                
    except Exception as e:
        print(f"❌ Ошибка WebSocket: {e}")
    finally:
        print("🔌 WebSocket соединение закрыто")

# === DATABASE OPERATIONS ===

def save_message_to_db(user_id, question, answer, role=None, specialization=None):
    """Сохранение сообщения в базу данных"""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO Messages (user_id, question, answer, role, specialization, timestamp)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        ''', (user_id, question, answer, role, specialization))
        conn.commit()
        print(f"💾 Сообщение сохранено в базу данных для пользователя {user_id}")
    except Exception as e:
        print(f"❌ Ошибка сохранения в базу данных: {e}")
    finally:
        conn.close()

# === API ENDPOINTS ===

@app.get("/")
async def root():
    """Информация о сервисе"""
    return {
        "service": "RAG Service - Context7 Enhanced",
        "version": "2.0",
        "status": "running",
        "features": [
            "Context7 Optimized Document Processing",
            "Enhanced Query Expansion", 
            "Smart Retriever Selection",
            "Advanced Metadata Enrichment",
            "WebSocket Streaming"
        ],
        "vector_stores": {
            "competency_lead": len(competency_lead_docs) if competency_lead_docs else 0,
            "intern": len(intern_docs) if intern_docs else 0,
            "specialist": len(specialist_docs) if specialist_docs else 0,
            "po": len(po_docs) if po_docs else 0,
            "full": len(full_docs) if full_docs else 0
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": "connected" if os.path.exists(DATABASE_URL) else "disconnected",
        "embeddings": "loaded",
        "retrievers_available": sum([
            1 for r in [embedding_retriever_competency_lead, embedding_retriever_intern, 
                       embedding_retriever_specialist, embedding_retriever_po, embedding_retriever_full] 
            if r is not None
        ])
    }

# === ПРОСТОЙ ЗАПУСК ===
if __name__ == "__main__":
    print("🚀 Запуск Context7-оптимизированного RAG сервиса...")
    print("🌐 Сервис будет доступен на http://localhost:8000")
    print("🔌 WebSocket endpoint: ws://localhost:8000/ws")
    uvicorn.run(app, host="0.0.0.0", port=8000)


