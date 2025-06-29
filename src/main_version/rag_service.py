import os
from dotenv import load_dotenv
import string
import asyncio
import sqlite3
import json
import re
from fastapi import FastAPI, WebSocket
import websockets
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import UnstructuredMarkdownLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.text_splitter import MarkdownHeaderTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import GigaChat
from langchain_gigachat import GigaChat
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.retrievers import EnsembleRetriever
import uvicorn

load_dotenv()

# Используем переменную окружения или относительный путь для локального запуска
DATABASE_URL = os.getenv("DATABASE_URL", "AI_agent.db")


# Инициализация FastAPI
app = FastAPI()

api_key = os.getenv("GIGACHAT_API_KEY")

# Новые пути к документам Markdown из папки docs/
folder_path_competency_lead = os.path.join(os.path.dirname(__file__), "docs/Competency_Lead")
folder_path_intern = os.path.join(os.path.dirname(__file__), "docs/Intern")
folder_path_specialist = os.path.join(os.path.dirname(__file__), "docs/Specialist")
folder_path_po = os.path.join(os.path.dirname(__file__), "docs/PO")
folder_path_full = os.path.join(os.path.dirname(__file__), "docs/full")

def create_docs_from_txt(folder_path):
    # Получаем список всех файлов .txt в указанной директории
    file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".txt")]

    # Список для хранения загруженных документов
    docs = []

    # Загружаем текст из файлов
    for file_path in file_paths:
        loader = TextLoader(file_path)
        docs.extend(loader.load())

    # Разделяем текст на чанки
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,  # Увеличено с 500 до 800 для лучшего контекста
        chunk_overlap=200  # Увеличено с 100 до 200 для лучшего перекрытия
    )
    split_docs = text_splitter.split_documents(docs)
    return split_docs

def create_docs_from_markdown_recursive(folder_path):
    """
    Рекурсивно загружает и обрабатывает Markdown документы из папки и всех вложенных папок
    """
    docs = []
    
    def scan_directory(directory):
        """Рекурсивно сканирует директорию для поиска .md файлов"""
        if not os.path.exists(directory):
            print(f"Папка {directory} не существует")
            return
        
        for root, dirs, files in os.walk(directory):
            md_files = [f for f in files if f.endswith(".md")]
            
            if md_files:
                print(f"Найдено {len(md_files)} .md файлов в {root}")
                
                # Настройка для разбивки по заголовкам Markdown
                headers_to_split_on = [
                    ("#", "Header 1"),
                    ("##", "Header 2"), 
                    ("###", "Header 3"),
                    ("####", "Header 4"),
                ]
                
                # Создаем splitter для заголовков
                markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
                
                # Загружаем и обрабатываем каждый файл
                for file in md_files:
                    file_path = os.path.join(root, file)
                    try:
                        # Используем UnstructuredMarkdownLoader для лучшей обработки Markdown
                        loader = UnstructuredMarkdownLoader(file_path)
                        file_docs = loader.load()
                        
                        # Разбиваем по заголовкам Markdown
                        for doc in file_docs:
                            md_header_splits = markdown_splitter.split_text(doc.page_content)
                            
                            # Если разбивка по заголовкам не дала результатов, используем обычную разбивку
                            if not md_header_splits:
                                text_splitter = RecursiveCharacterTextSplitter(
                                    chunk_size=800,
                                    chunk_overlap=200,
                                    separators=["\n\n", "\n", " ", ""]
                                )
                                md_header_splits = text_splitter.split_documents([doc])
                            
                            # Добавляем информацию о папке в метаданные
                            for split_doc in md_header_splits:
                                if hasattr(split_doc, 'metadata'):
                                    split_doc.metadata['folder_path'] = root
                                    split_doc.metadata['relative_path'] = os.path.relpath(root, directory)
                                
                            docs.extend(md_header_splits)
                            
                    except Exception as e:
                        print(f"Ошибка при загрузке файла {file_path}: {e}")
                        # Если не удается загрузить как Markdown, пробуем как обычный текст
                        try:
                            loader = TextLoader(file_path)
                            fallback_docs = loader.load()
                            text_splitter = RecursiveCharacterTextSplitter(
                                chunk_size=800,
                                chunk_overlap=200
                            )
                            split_fallback = text_splitter.split_documents(fallback_docs)
                            
                            # Добавляем метаданные
                            for split_doc in split_fallback:
                                if hasattr(split_doc, 'metadata'):
                                    split_doc.metadata['folder_path'] = root
                                    split_doc.metadata['relative_path'] = os.path.relpath(root, directory)
                            
                            docs.extend(split_fallback)
                        except Exception as fallback_error:
                            print(f"Критическая ошибка при загрузке файла {file_path}: {fallback_error}")
    
    scan_directory(folder_path)
    print(f"Всего загружено документов из {folder_path}: {len(docs)}")
    return docs

def create_docs_adaptive(folder_path):
    """
    Универсальная функция для загрузки документов (.txt или .md)
    Теперь с приоритетом на .md файлы и рекурсивный поиск
    """
    if not os.path.exists(folder_path):
        print(f"Папка {folder_path} не существует")
        return []
    
    # Проверяем наличие .md файлов рекурсивно
    md_files_found = False
    for root, dirs, files in os.walk(folder_path):
        if any(f.endswith(".md") for f in files):
            md_files_found = True
            break
    
    if md_files_found:
        print(f"Найдены Markdown файлы в {folder_path}, используем рекурсивный Markdown загрузчик")
        return create_docs_from_markdown_recursive(folder_path)
    else:
        # Fallback для старых .txt файлов (если нужно)
        txt_files = []
        for root, dirs, files in os.walk(folder_path):
            txt_files.extend([f for f in files if f.endswith(".txt")])
        
        if txt_files:
            print(f"Найдены текстовые файлы в {folder_path}, используем текстовый загрузчик")
            return create_docs_from_txt(folder_path)
        else:
            print(f"В папке {folder_path} не найдены поддерживаемые файлы (.txt или .md)")
            return []

# Создание новых векторных баз на основе структуры docs/
print("=== Инициализация новых векторных баз ===")

# 1. Векторная база для Competency Lead (Лидов компетенций)
print("Загружаем документы для Competency Lead...")
split_docs_competency_lead = create_docs_adaptive(folder_path_competency_lead)

# 2. Векторная база для Intern (Стажеров)
print("Загружаем документы для Intern...")
split_docs_intern = create_docs_adaptive(folder_path_intern)

# 3. Векторная база для Specialist (Специалистов) 
print("Загружаем документы для Specialist...")
split_docs_specialist = create_docs_adaptive(folder_path_specialist)

# 4. Векторная база для PO/PM (Product Owner/Project Manager)
print("Загружаем документы для PO/PM...")
split_docs_po = create_docs_adaptive(folder_path_po)

# 5. Полная векторная база для свободных вопросов (ID 777, 888, 999)
print("Загружаем документы для полной базы...")
split_docs_full = create_docs_adaptive(folder_path_full)

# Инициализация модели для эмбеддингов
print("Инициализация модели эмбеддингов...")
model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': False}
embedding = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

# Создание новых векторных хранилищ
print("Создание векторных хранилищ...")

# 1. Векторное хранилище для Competency Lead
if split_docs_competency_lead:
    vector_store_competency_lead = FAISS.from_documents(split_docs_competency_lead, embedding=embedding)
    embedding_retriever_competency_lead = vector_store_competency_lead.as_retriever(search_kwargs={"k": 10})
    print(f"✅ Создано хранилище для Competency Lead: {len(split_docs_competency_lead)} документов")
else:
    print("⚠️ Нет документов для Competency Lead")
    embedding_retriever_competency_lead = None

# 2. Векторное хранилище для Intern
if split_docs_intern:
    vector_store_intern = FAISS.from_documents(split_docs_intern, embedding=embedding)
    embedding_retriever_intern = vector_store_intern.as_retriever(search_kwargs={"k": 10})
    print(f"✅ Создано хранилище для Intern: {len(split_docs_intern)} документов")
else:
    print("⚠️ Нет документов для Intern")
    embedding_retriever_intern = None

# 3. Векторное хранилище для Specialist
if split_docs_specialist:
    vector_store_specialist = FAISS.from_documents(split_docs_specialist, embedding=embedding)
    embedding_retriever_specialist = vector_store_specialist.as_retriever(search_kwargs={"k": 10})
    print(f"✅ Создано хранилище для Specialist: {len(split_docs_specialist)} документов")
else:
    print("⚠️ Нет документов для Specialist")
    embedding_retriever_specialist = None

# 4. Векторное хранилище для PO/PM
if split_docs_po:
    vector_store_po = FAISS.from_documents(split_docs_po, embedding=embedding)
    embedding_retriever_po = vector_store_po.as_retriever(search_kwargs={"k": 10})
    print(f"✅ Создано хранилище для PO/PM: {len(split_docs_po)} документов")
else:
    print("⚠️ Нет документов для PO/PM")
    embedding_retriever_po = None

# 5. Полное векторное хранилище для свободных вопросов
if split_docs_full:
    vector_store_full = FAISS.from_documents(split_docs_full, embedding=embedding)
    embedding_retriever_full = vector_store_full.as_retriever(search_kwargs={"k": 15})
    print(f"✅ Создано полное хранилище: {len(split_docs_full)} документов")
else:
    print("⚠️ Нет документов для полной базы")
    embedding_retriever_full = None

print("=== Инициализация векторных баз завершена ===")

# Совместимость: создаем fallback на полную базу если отдельные базы не созданы
if not embedding_retriever_competency_lead:
    embedding_retriever_competency_lead = embedding_retriever_full
if not embedding_retriever_intern:
    embedding_retriever_intern = embedding_retriever_full  
if not embedding_retriever_specialist:
    embedding_retriever_specialist = embedding_retriever_full
if not embedding_retriever_po:
    embedding_retriever_po = embedding_retriever_full

# Инициализация модели GigaChat

def create_retrieval_chain_from_folder(role, specialization, question_id, embedding_retriever, prompt_template):
    
    # Заполнение шаблона промпта
    template = string.Template(prompt_template)
    filled_prompt = template.substitute(role=role, specialization=specialization)

    # Создание промпта
    prompt = ChatPromptTemplate.from_template(filled_prompt)

    llm = GigaChat(
        credentials=api_key,
        model='GigaChat-2',
        verify_ssl_certs=False,
        profanity_check=False
    )

    # Создание цепочки для работы с документами
    document_chain = create_stuff_documents_chain(
        llm=llm,
        prompt=prompt
    )

    # Создание retrieval_chain
    retrieval_chain = create_retrieval_chain(embedding_retriever, document_chain)

    return retrieval_chain

def get_prompt_from_db(question_id):
    try:
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        cursor.execute("SELECT prompt_template FROM Prompts WHERE question_id = ?", (question_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            print(f"✅ Промпт для ID {question_id} найден в БД")
            return result[0]
        else:
            print(f"❌ Промпт для ID {question_id} НЕ найден в БД")
            return None
    except sqlite3.Error as e:
        print(f"❌ Ошибка при получении промпта из БД: {e}")
        return None

def get_best_retriever_for_role_spec(role, specialization):
    """
    Выбирает лучший retriever на основе роли и специализации
    Обновлено для новой архитектуры с 5 векторными базами
    """
    role_lower = role.lower() if role else ""
    spec_lower = specialization.lower() if specialization else ""
    
    print(f"🔍 Выбор retriever для роли: '{role}', специализации: '{specialization}'")
    
    # Маппинг ролей на новые retrievers
    if 'лид' in role_lower and 'компетенц' in role_lower:
        print("→ Выбран retriever для Competency Lead")
        return embedding_retriever_competency_lead
    elif 'стажер' in role_lower or 'intern' in role_lower.replace(' ', ''):
        print("→ Выбран retriever для Intern")
        return embedding_retriever_intern
    elif 'специалист' in role_lower or 'specialist' in role_lower.replace(' ', ''):
        print("→ Выбран retriever для Specialist")
        return embedding_retriever_specialist
    elif 'po' in role_lower or 'pm' in role_lower or 'product owner' in role_lower or 'project manager' in role_lower:
        print("→ Выбран retriever для PO/PM")
        return embedding_retriever_po
    else:
        # Если роль неопределенная, выбираем по специализации или используем полную базу
        if spec_lower in ['аналитик', 'тестировщик', 'python', 'java', 'web']:
            print("→ Роль неопределенная, но есть специализация - используем Specialist")
            return embedding_retriever_specialist
        else:
            print("→ Неопределенная роль/специализация - используем полную базу")
            return embedding_retriever_full

async def generate_semantic_search_queries(question, role, specialization):
    """
    Генерирует семантически связанные поисковые запросы для улучшения векторного поиска
    """
    # Создаем LLM для генерации альтернативных запросов
    llm = GigaChat(
        credentials=api_key,
        model='GigaChat-2',
        verify_ssl_certs=False,
        profanity_check=False
    )
    
    # Специализированные ключевые термины для разных ролей
    role_specific_terms = {
        'тестировщик': ['тестирование', 'качество', 'баги', 'QA', 'стратегия тестирования', 'критерии приемки'],
        'qa': ['тестирование', 'качество', 'баги', 'QA', 'стратегия тестирования', 'критерии приемки'],
        'аналитик': ['анализ требований', 'документация', 'бизнес-процессы', 'стейкхолдеры'],
        'python': ['разработка', 'код', 'архитектура', 'техническое решение', 'программирование'],
        'java': ['разработка', 'код', 'архитектура', 'техническое решение', 'программирование'],
        'web': ['фронтенд', 'интерфейс', 'UX', 'веб-разработка', 'пользовательский опыт']
    }
    
    spec_lower = specialization.lower() if specialization else ""
    specific_terms = []
    for key, terms in role_specific_terms.items():
        if key in spec_lower:
            specific_terms = terms
            break
    
    # Если специализация не найдена, используем общие термины
    if not specific_terms:
        specific_terms = ['профессиональное развитие', 'компетенции', 'навыки']
    
    # Промпт для генерации альтернативных поисковых запросов
    query_generation_prompt = f"""
Дан вопрос: "{question}"
Роль пользователя: {role if role else "не указана"}
Специализация: {specialization if specialization else "не указана"}

Сгенерируй 5-6 альтернативных поисковых запросов для поиска в корпоративной базе знаний по карьерному развитию, ИПР, лидерству и управлению командой в IT.

ВАЖНО: Учитывай специализацию {specialization} и используй специфичные термины: {', '.join(specific_terms)}

Альтернативные запросы должны:
1. Включать точные фразы из корпоративных документов
2. Фокусироваться на конкретных практиках для специализации {specialization}
3. Использовать базовые термины: "ИПР", "индивидуальный план развития", "лид компетенции", "ожидания", "встречи 1-2-1", "цели развития", "компетенции", "обратная связь"
4. Использовать специализированные термины: {', '.join(specific_terms)}
5. Быть короткими и точными для векторного поиска
6. Покрывать разные аспекты работы {specialization} с PO/PM

Примеры запросов для {specialization}:
- "взаимодействие {specialization} PO PM"
- "ожидания от PO PM {specialization}"
- "{specific_terms[0] if specific_terms else 'развитие'} специалист команда"
- "обратная связь {specialization} проект"

Ответь только списком из 5-6 запросов, каждый с новой строки, без нумерации и дополнительного текста:
"""
    
    try:
        response = await llm.ainvoke(query_generation_prompt)
        alternative_queries = [q.strip() for q in response.content.split('\n') if q.strip()]
        
        # Добавляем исходный вопрос в начало списка
        all_queries = [question] + alternative_queries
        
        print(f"Сгенерированы поисковые запросы:")
        for i, query in enumerate(all_queries, 1):
            print(f"  {i}. {query}")
        
        return all_queries
        
    except Exception as e:
        print(f"Ошибка при генерации альтернативных запросов: {e}")
        return [question]  # Возвращаем только исходный вопрос в случае ошибки

async def enhanced_vector_search(question, role, specialization, embedding_retriever, top_k=8):
    """
    Улучшенный векторный поиск с использованием множественных семантических запросов
    """
    # Генерируем альтернативные поисковые запросы
    search_queries = await generate_semantic_search_queries(question, role, specialization)
    
    # Собираем все найденные документы
    all_docs = []
    doc_scores = {}  # Для подсчета "голосов" за каждый документ
    
    for query in search_queries:
        try:
            # Выполняем поиск для каждого запроса
            docs = await embedding_retriever.ainvoke(query)
            
            # Добавляем документы с весами (первые запросы важнее)
            weight = 1.0 / (search_queries.index(query) + 1)  # Убывающий вес
            
            for i, doc in enumerate(docs):
                doc_id = doc.metadata.get('source', '') + str(hash(doc.page_content[:100]))
                
                # Увеличиваем счетчик для документа
                if doc_id not in doc_scores:
                    doc_scores[doc_id] = {
                        'doc': doc,
                        'score': 0,
                        'query_matches': []
                    }
                
                # Добавляем взвешенный балл (документы в топе получают больше баллов)
                position_weight = 1.0 / (i + 1)
                doc_scores[doc_id]['score'] += weight * position_weight
                doc_scores[doc_id]['query_matches'].append(query)
        
        except Exception as e:
            print(f"Ошибка поиска для запроса '{query}': {e}")
            continue
    
    # Сортируем документы по общему счету
    sorted_docs = sorted(doc_scores.values(), key=lambda x: x['score'], reverse=True)
    
    # Возвращаем топ-K документов
    result_docs = [item['doc'] for item in sorted_docs[:top_k]]
    
    print(f"\nРезультаты улучшенного векторного поиска:")
    for i, item in enumerate(sorted_docs[:top_k], 1):
        doc = item['doc']
        score = item['score']
        source = doc.metadata.get('source', 'Неизвестно')
        print(f"  {i}. Счет: {score:.3f} | Источник: {source.split('/')[-1]}")
        print(f"     Совпадения с запросами: {len(item['query_matches'])}")
        print(f"     Запросы: {item['query_matches'][:2]}")  # Показываем первые 2 запроса
        print(f"     Содержимое: {doc.page_content[:150]}...")
        print()
    
    return result_docs

async def create_enhanced_retrieval_chain(role, specialization, question_id, embedding_retriever, prompt_template):
    """
    Создает улучшенную retrieval chain с семантическим векторным поиском и поддержкой стриминга
    """
    # Заполнение шаблона промпта
    template = string.Template(prompt_template)
    filled_prompt = template.substitute(
        role=role,
        specialization=specialization
    )
    
    # Создание LLM
    llm = GigaChat(
        credentials=api_key,
        model='GigaChat-2',
        verify_ssl_certs=False,
        profanity_check=False
    )
    
    # Создаем объект, который поддерживает метод astream
    class EnhancedRetrievalChain:
        def __init__(self, llm, filled_prompt, role, specialization, embedding_retriever, question_id):
            self.llm = llm
            self.base_prompt = filled_prompt
            self.role = role
            self.specialization = specialization
            self.embedding_retriever = embedding_retriever
            self.question_id = question_id

        async def astream(self, input_data):
            """
            Асинхронный стриминг с улучшенным поиском и генерацией ответа.
            """
            question = input_data.get('input', '')
            dialogue_context = input_data.get('dialogue_context', '[]')

            # 1. Используем улучшенный поиск для получения релевантных документов
            docs = await enhanced_vector_search(question, self.role, self.specialization, self.embedding_retriever)
            
            # 2. Формируем контекст из документов
            context_text = "\n\n".join([doc.page_content for doc in docs])
            
            # 3. Формируем финальный промпт
            dialogue_history_prompt_part = ""
            if dialogue_context and dialogue_context != '[]':
                dialogue_history_prompt_part = f"\n\nКонтекст предыдущих сообщений:\n{dialogue_context}"

            final_prompt = f"{self.base_prompt}{dialogue_history_prompt_part}\n\nКонтекст из документов:\n{context_text}\n\nВопрос: {question}\n\nОтвет:"
            
            # Отладочная информация
            print(f"\n--- FINAL PROMPT для ID={self.question_id} ---\n{final_prompt[:500]}...\n--- END PROMPT ---\n")
            
            # 4. Стримим ответ от LLM
            try:
                chunk_count = 0
                async for chunk in self.llm.astream(final_prompt):
                    if chunk and chunk.content:
                        chunk_count += 1
                        print(f"📤 RAG chunk #{chunk_count}: {chunk.content[:50]}...")
                        yield {"answer": chunk.content}
                
                print(f"✅ RAG стриминг завершен. Всего chunks: {chunk_count}")
                if chunk_count == 0:
                    print("❌ ВНИМАНИЕ: GigaChat не вернул ни одного chunk для RAG!")
                    yield {"answer": "Извините, не удалось получить ответ. Попробуйте переформулировать вопрос."}
                    
            except Exception as e:
                print(f"❌ ОШИБКА в стриминге LLM: {e}")
                yield {"answer": f"Произошла ошибка при генерации ответа: {e}"}

    return EnhancedRetrievalChain(llm, filled_prompt, role, specialization, embedding_retriever, question_id)

async def create_enhanced_retrieval_chain_for_suggestions(role, specialization, user_question, bot_answer, embedding_retriever, prompt_template):
    """
    Создает улучшенную retrieval chain для генерации связанных вопросов (промпт 999)
    """
    # Заполнение шаблона промпта со всеми необходимыми переменными
    template = string.Template(prompt_template)
    filled_prompt = template.substitute(
        role=role,
        specialization=specialization,
        user_question=user_question,
        bot_answer=bot_answer
    )
    
    # Создание LLM
    llm = GigaChat(
        credentials=api_key,
        model='GigaChat-2',
        verify_ssl_certs=False,
        profanity_check=False
    )
    
    # Создаем кастомную функцию для обработки запроса
    async def enhanced_suggestions_process(input_data):
        search_query = input_data.get('input', '')
        
        print(f"Генерируем связанные вопросы с улучшенным векторным поиском: {search_query}")
        
        # Выполняем улучшенный векторный поиск
        relevant_docs = await enhanced_vector_search(search_query, role, specialization, embedding_retriever)
        
        # Формируем контекст из найденных документов
        context = "\n\n".join([doc.page_content for doc in relevant_docs])
        
        # Создаем финальный промпт с контекстом
        final_prompt = f"""{filled_prompt}

Дополнительный контекст из корпоративных документов:
{context}

Используй этот контекст для генерации более релевантных и специфичных вопросов, связанных с ролью {role} и специализацией {specialization}."""
        
        print(f"Отправляем запрос в GigaChat для генерации связанных вопросов...")
        
        # Получаем ответ от LLM
        response = await llm.ainvoke(final_prompt)
        
        return {"answer": response.content}
    
    return enhanced_suggestions_process

async def check_document_relevance(question, embedding_retriever, threshold=0.5):
    """
    Проверяет релевантность найденных документов для вопроса.
    Возвращает True если найдены релевантные документы, False если нет.
    """
    try:
        # Получаем топ-3 документа для быстрой проверки релевантности
        docs = await embedding_retriever.ainvoke(question)
        if not docs:
            return False
        
        # Простая эвристика: проверяем наличие ключевых слов из вопроса в документах
        question_words = set(question.lower().split())
        # Убираем стоп-слова
        stop_words = {'что', 'как', 'где', 'когда', 'почему', 'кто', 'какой', 'можно', 'нужно', 'я', 'мне', 'и', 'в', 'на', 'с', 'по', 'для', 'от', 'до', 'из', 'к', 'о', 'об'}
        question_words = question_words - stop_words
        
        if len(question_words) == 0:
            return True  # Если нет содержательных слов, считаем релевантным
        
        # Проверяем первые 3 документа
        relevant_count = 0
        for doc in docs[:3]:
            doc_text = doc.page_content.lower()
            # Считаем совпадения ключевых слов
            matches = sum(1 for word in question_words if word in doc_text)
            if matches >= min(2, len(question_words) * 0.3):  # Минимум 2 слова или 30% от ключевых слов
                relevant_count += 1
        
        # Считаем релевантными если хотя бы один из топ-3 документов содержит ключевые слова
        is_relevant = relevant_count > 0
        
        print(f"🔍 Проверка релевантности: '{question[:50]}...'")
        print(f"   Ключевые слова: {list(question_words)[:5]}")
        print(f"   Проверено документов: {min(3, len(docs))}")
        print(f"   Релевантных: {relevant_count}")
        print(f"   Результат: {'РЕЛЕВАНТНО' if is_relevant else 'НЕ РЕЛЕВАНТНО'}")
        
        return is_relevant
        
    except Exception as e:
        print(f"❌ Ошибка при проверке релевантности: {e}")
        return True  # В случае ошибки считаем релевантным (используем RAG)

#mplusk1
@app.websocket("/ws_suggest")
async def websocket_suggest_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("ws_suggest: connection accepted")
    data = await websocket.receive_text()
    print(f"ws_suggest: received data: {data}")
    payload = json.loads(data)
    
    user_question = payload.get("user_question")
    bot_answer = payload.get("bot_answer")
    role = payload.get("role")
    specialization = payload.get("specialization")

    prompt_template = get_prompt_from_db(999)
    if not prompt_template:
        print("ws_suggest: ERROR - Prompt 999 not found")
        await websocket.send_text(json.dumps({"error": "Prompt not found"}))
        await websocket.close()
        return

    # Всегда используем RAG для генерации связанных вопросов (промпт 999)
    use_rag = True
    print(f"ws_suggest: Using RAG for question generation")
    
    if use_rag:
        # Используем RAG для более точной генерации вопросов
        embedding_retriever = get_best_retriever_for_role_spec(role, specialization)
        
        # Создаем специальную retrieval chain для генерации связанных вопросов (промпт 999)
        retrieval_chain = await create_enhanced_retrieval_chain_for_suggestions(
            role=role,
            specialization=specialization,
            user_question=user_question,
            bot_answer=bot_answer,
            embedding_retriever=embedding_retriever,
            prompt_template=prompt_template
        )
        
        try:
            print("ws_suggest: Using RAG-enhanced question generation...")
            # Формируем запрос для поиска релевантных документов
            search_query = f"Вопросы по теме: {user_question}. Роль: {role}. Специализация: {specialization}"
            
            # Вызываем функцию напрямую, так как она возвращает функцию
            response = await retrieval_chain({'input': search_query})
            raw_response = response.get('answer', '')
            print(f"ws_suggest: RAG response: {raw_response}")
            
            # Парсим ответ
            cleaned_response = re.sub(r'^\s*\d+\.\s*', '', raw_response, flags=re.MULTILINE)
            questions = [q.strip() for q in cleaned_response.split('\n') if q.strip() and len(q.strip()) > 10]
            
            # Ограничиваем до 5 вопросов
            questions = questions[:5]
            
        except Exception as e:
            print(f"ws_suggest: ERROR in RAG call: {e}, falling back to direct LLM")
            use_rag = False
    
    if not use_rag:
        # Используем прямое обращение к LLM без RAG
        template = string.Template(prompt_template)
        filled_prompt = template.substitute(
            user_question=user_question,
            bot_answer=bot_answer,
            role=role,
            specialization=specialization
        )

        # Добавляем инструкции по генерации релевантных вопросов
        question_generation_guidance = f"""
Учитывая, что пользователь имеет роль '{role}' и специализацию '{specialization}',
сгенерируйте 3-5 релевантных вопросов, которые:
1. Соответствуют текущему контексту диалога
2. Учитывают специфику роли и специализации пользователя
3. Помогают углубить понимание обсуждаемой темы
4. Могут быть полезны для профессионального развития в рамках специализации
5. Не выходят за рамки компетенций пользователя

Формат ответа: каждый вопрос с новой строки, без нумерации.
"""
        filled_prompt += question_generation_guidance

        llm = GigaChat(
            credentials=api_key,
            model='GigaChat-2',
            verify_ssl_certs=False,
            profanity_check=False
        )
        
        try:
            print(f"ws_suggest: Using direct LLM for question generation...")
            response = await llm.ainvoke(filled_prompt)
            print(f"ws_suggest: LLM response: {response.content}")
            
            # Удаляем нумерацию, чтобы обеспечить корректный парсинг
            cleaned_response = re.sub(r'^\s*\d+\.\s*', '', response.content, flags=re.MULTILINE)
            questions = [q.strip() for q in cleaned_response.split('\n') if q.strip()]
        except Exception as e:
            print(f"ws_suggest: ERROR in LLM call: {e}")
            await websocket.send_text(json.dumps({"error": str(e)}))
            await websocket.close()
            return

    print(f"ws_suggest: Final questions: {questions}")
    await websocket.send_text(json.dumps(questions))
    print(f"ws_suggest: Sent questions to client: {json.dumps(questions)}")
    await websocket.close()
    print("ws_suggest: connection closed")
#mplusk2
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Обрабатывает WebSocket соединение и передает стриминг ответа GigaChat."""
    await websocket.accept()
    question = await websocket.receive_text()
    role = await websocket.receive_text()
    specialization = await websocket.receive_text()
    question_id = await websocket.receive_text()
    context = await websocket.receive_text()
    print(context)
    count = await websocket.receive_text()
    question_id = int(question_id)
    count = int(count)
    print(question)
    print(role)
    print(specialization)
    print(f"количество {count}")
    print(f"айди {question_id}")
    print(f"🔍 Получаем промпт для ID={question_id}")
    prompt_template = get_prompt_from_db(question_id)
    print(f"📝 Промпт получен: {bool(prompt_template)}")
    if not prompt_template:
        print(f"⚠️ Промпт для ID={question_id} не найден, используем fallback 777")
        prompt_template = get_prompt_from_db(777)
        print(f"📝 Fallback промпт получен: {bool(prompt_template)}")
    
    if not prompt_template:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: Не удалось получить промпт для ID={question_id} или fallback 777")
        await websocket.send_text("Ошибка: не удалось загрузить промпт. Обратитесь к администратору.")
        return
    
    # Новая логика выбора retriever для работы с 5 векторными базами
    embedding_retriever = embedding_retriever_full  # По умолчанию полная база
    use_rag_for_special = False
    
    # Проверяем тип промпта и выбираем стратегию
    if question_id in [777, 888, 999]:
        print(f"🔍 Специальный ID {question_id}: проверяем релевантность документов")
        use_rag_for_special = await check_document_relevance(question, embedding_retriever_full)
        if use_rag_for_special:
            print(f"✅ Документы релевантны для ID {question_id} - используем RAG с полной базой")
            embedding_retriever = embedding_retriever_full
        else:
            print(f"❌ Документы НЕ релевантны для ID {question_id} - ответ без RAG")
    else:
        # Для обычных вопросов выбираем retriever на основе роли и специализации
        print(f"📋 Обычный вопрос ID={question_id}: выбираем retriever по роли/специализации")
        embedding_retriever = get_best_retriever_for_role_spec(role, specialization)
        
        # Если выбранный retriever None, используем полную базу как fallback
        if embedding_retriever is None:
            print("⚠️ Выбранный retriever недоступен, используем полную базу")
            embedding_retriever = embedding_retriever_full
    
    print(f"📊 Состояние для ID {question_id}:")
    print(f"   - use_rag_for_special: {use_rag_for_special}")
    print(f"   - embedding_retriever: {'настроен' if embedding_retriever else 'НЕ настроен'}")
    print(f"   - question: {question[:100]}...")
    print(f"   - role: {role}")
    print(f"   - specialization: {specialization}")
    print(f"   - context: {context[:100] if context else 'None'}...")

    # Создаем retrieval_chain для вопросов, которые его используют
    retrieval_chain = None
    should_use_rag = (
        question_id not in [777, 888, 999] or  # Обычные промпты всегда используют RAG
        (question_id in [777, 888, 999] and use_rag_for_special)  # Специальные только при релевантности
    )
    
    if should_use_rag:
        # Используем улучшенный поиск для ВСЕХ типов вопросов
        print(f"Используем улучшенный векторный поиск для question_id={question_id}")
        retrieval_chain = await create_enhanced_retrieval_chain(
            role=role,
            specialization=specialization,
            question_id=question_id,
            embedding_retriever=embedding_retriever,
            prompt_template=prompt_template
        )

    # Убираем очистку от символов форматирования - они нужны для Markdown!
    
    
    # Fallback без RAG для специальных ID когда документы нерелевантны
    if question_id in [777, 888, 999] and not use_rag_for_special:
        print(f"Обрабатываем специальный промпт {question_id} БЕЗ RAG...")
        
        # Формируем промпт
        template = string.Template(prompt_template)
        filled_prompt = template.substitute(
            role=role,
            specialization=specialization
        )
        
        # Для ID=888 добавляем контекст диалога
        if question_id == 888:
            if context and context != "[]":
                context_info = f"\n\nКонтекст предыдущих сообщений:\n{context}\n\n"
                full_prompt = filled_prompt + context_info + f"Вопрос пользователя: {question}"
            else:
                full_prompt = filled_prompt + f"\n\nВопрос пользователя: {question}"
        else:
            # Для ID=777, 999 без контекста диалога
            full_prompt = filled_prompt + f"\n\nВопрос пользователя: {question}"
        
        # Добавляем улучшенную инструкцию по форматированию
        full_prompt += """

КРИТИЧЕСКИ ВАЖНО - ФОРМАТИРОВАНИЕ ОТВЕТА:
Отформатируй свой ответ строго в формате Markdown с соблюдением следующих правил:

1. **ЗАГОЛОВКИ** (обязательно с пробелами после #):
   - # Основной заголовок ответа
   - ## Роли и уровни (например: ## Product Owner (PO):)
   - ### Конкретные уровни (например: ### Middle-аналитик)
   
2. **СТРУКТУРА ОТВЕТА**:
   - Начинай с основного заголовка # 
   - Каждую роль выделяй заголовком ##
   - Каждый уровень внутри роли выделяй заголовком ###
   - После каждого заголовка ОБЯЗАТЕЛЬНО пустая строка

3. **СПИСКИ** (обязательно с пробелами):
   - Для нумерованных: 1. пункт 2. пункт 3. пункт
   - Для маркированных: - пункт или * пункт
   - После двоеточия (:) переходи на новую строку для списка

4. **ВЫДЕЛЕНИЕ ТЕКСТА**:
   - **Жирный текст** для ключевых терминов
   - *Курсив* для акцентов
   - `код` для технических терминов

5. **ЗАПРЕЩЕНО**:
   - НЕ используй ### или ## в середине текста без создания заголовка
   - НЕ пиши длинные абзацы без разбивки
   - НЕ забывай пустые строки между разделами

ПРИМЕР ПРАВИЛЬНОГО ФОРМАТИРОВАНИЯ:
# Ожидания от Лида Компетенции

## Product Owner (PO):

### Middle-аналитик

- Проведение анализа текущих процессов
- Создание диаграмм и моделей
- Помощь в формулировке требований

### Senior-аналитик

- Владение стратегиями тестирования
- Опыт работы с командой

Следуй этому формату СТРОГО!"""
        
        print(f"\n--- PROMPT ДЛЯ LLM (ID={question_id}, без RAG) ---\n")
        print(full_prompt)
        print("\n--- КОНЕЦ PROMPT ---\n")
        
        try:
            print("Начинаем стриминг ответа от GigaChat...")
            chunk_count = 0
            # Используем GigaChat для ответа
            async for chunk in GigaChat(
                credentials=api_key,
                verify_ssl_certs=False,
                model='GigaChat-2'
            ).astream(full_prompt):
                if chunk and chunk.content:
                    chunk_count += 1
                    answer = chunk.content.strip()
                    
                    # Оставляем ответ как есть для сохранения Markdown форматирования
                    
                    print(f"Отправляем chunk #{chunk_count}: {answer[:50]}...")
                    await websocket.send_text(answer)
            
            print(f"Стриминг завершен. Всего отправлено chunks: {chunk_count}")
            if chunk_count == 0:
                print("ВНИМАНИЕ: GigaChat не вернул ни одного chunk!")
                await websocket.send_text("Извините, не удалось получить ответ. Попробуйте переформулировать вопрос.")
                
        except Exception as e:
            print(f"ОШИБКА при работе с GigaChat для ID={question_id}: {e}")
            await websocket.send_text(f"Произошла ошибка при обработке вопроса: {str(e)}")
    
    elif should_use_rag and retrieval_chain is not None:
        # Используем RAG для обычных промптов или для специальных промптов при релевантности
        print(f"Используем RAG для промпта {question_id}")
        
        # Для промпта 888 передаем контекст диалога в chain
        dialogue_context_for_chain = "[]"
        if question_id == 888 and context and context != "[]":
            dialogue_context_for_chain = context
            
        # Используем стриминг для всех промптов одинаково
        async for chunk in retrieval_chain.astream({'input': question, 'dialogue_context': dialogue_context_for_chain}):
            if chunk:
                # Извлекаем ответ
                answer = chunk.get("answer", "").strip()

                # Оставляем ответ как есть для сохранения Markdown форматирования
                    
                await websocket.send_text(answer)  # Отправляем очищенный текстовый ответ

    elif not should_use_rag and question_id not in [777, 888, 999]:
        # Fallback для обычных промптов без RAG (не должно происходить)
        print(f"ВНИМАНИЕ: Обычный промпт {question_id} обрабатывается без RAG!")
        template = string.Template(prompt_template)
        filled_prompt = template.substitute(role=role, specialization=specialization)
        full_prompt = filled_prompt + f"\n\nВопрос пользователя: {question}"
        
        # Добавляем улучшенную инструкцию по форматированию
        full_prompt += """

КРИТИЧЕСКИ ВАЖНО - ФОРМАТИРОВАНИЕ ОТВЕТА:
Отформатируй свой ответ строго в формате Markdown с соблюдением следующих правил:

1. **ЗАГОЛОВКИ** (обязательно с пробелами после #):
   - # Основной заголовок ответа
   - ## Роли и уровни (например: ## Product Owner (PO):)
   - ### Конкретные уровни (например: ### Middle-аналитик)
   
2. **СТРУКТУРА ОТВЕТА**:
   - Начинай с основного заголовка # 
   - Каждую роль выделяй заголовком ##
   - Каждый уровень внутри роли выделяй заголовком ###
   - После каждого заголовка ОБЯЗАТЕЛЬНО пустая строка

3. **СПИСКИ** (обязательно с пробелами):
   - Для нумерованных: 1. пункт 2. пункт 3. пункт
   - Для маркированных: - пункт или * пункт
   - После двоеточия (:) переходи на новую строку для списка

4. **ВЫДЕЛЕНИЕ ТЕКСТА**:
   - **Жирный текст** для ключевых терминов
   - *Курсив* для акцентов
   - `код` для технических терминов

5. **ЗАПРЕЩЕНО**:
   - НЕ используй ### или ## в середине текста без создания заголовка
   - НЕ пиши длинные абзацы без разбивки
   - НЕ забывай пустые строки между разделами

ПРИМЕР ПРАВИЛЬНОГО ФОРМАТИРОВАНИЯ:
# Ожидания от Лида Компетенции

## Product Owner (PO):

### Middle-аналитик

- Проведение анализа текущих процессов
- Создание диаграмм и моделей
- Помощь в формулировке требований

### Senior-аналитик

- Владение стратегиями тестирования
- Опыт работы с командой

Следуй этому формату СТРОГО!"""
        
        try:
            async for chunk in GigaChat(
                credentials=api_key,
                verify_ssl_certs=False,
                model='GigaChat-2'
            ).astream(full_prompt):
                if chunk and chunk.content:
                    answer = chunk.content.strip()
                    # Оставляем ответ как есть для сохранения Markdown форматирования
                    await websocket.send_text(answer)
        except Exception as e:
            print(f"ОШИБКА при fallback для промпта {question_id}: {e}")
            await websocket.send_text(f"Произошла ошибка: {str(e)}")

    elif(count > 1 and count < 10):
        prompt = f"""Использую контекст нашей прошлой беседы {context}, ответь на уточняющий вопрос {question}.

КРИТИЧЕСКИ ВАЖНО - ФОРМАТИРОВАНИЕ ОТВЕТА:
Отформатируй свой ответ строго в формате Markdown с соблюдением следующих правил:

1. **ЗАГОЛОВКИ** (обязательно с пробелами после #):
   - # Основной заголовок ответа
   - ## Роли и уровни (например: ## Product Owner (PO):)
   - ### Конкретные уровни (например: ### Middle-аналитик)
   
2. **СТРУКТУРА ОТВЕТА**:
   - Начинай с основного заголовка # 
   - Каждую роль выделяй заголовком ##
   - Каждый уровень внутри роли выделяй заголовком ###
   - После каждого заголовка ОБЯЗАТЕЛЬНО пустая строка

3. **СПИСКИ** (обязательно с пробелами):
   - Для нумерованных: 1. пункт 2. пункт 3. пункт
   - Для маркированных: - пункт или * пункт
   - После двоеточия (:) переходи на новую строку для списка

4. **ВЫДЕЛЕНИЕ ТЕКСТА**:
   - **Жирный текст** для ключевых терминов
   - *Курсив* для акцентов
   - `код` для технических терминов

5. **ЗАПРЕЩЕНО**:
   - НЕ используй ### или ## в середине текста без создания заголовка
   - НЕ пиши длинные абзацы без разбивки
   - НЕ забывай пустые строки между разделами

ВАЖНО: НЕ используй символы ### или ## в середине текста без создания заголовка. Если нужно упомянуть роль, используй **жирное выделение**.
"""
        for chunk in GigaChat(credentials=api_key,
                              verify_ssl_certs=False,
                                model='GigaChat-2'
                                ).stream(prompt):
            answer = chunk.content.strip()  # Используем атрибут .content

            # Отправляем ответ через WebSocket
            await websocket.send_text(answer)


    elif(count == 101):
        for chunk in GigaChat(credentials=api_key,
                              verify_ssl_certs=False,
                                model='GigaChat-2'
                                ).stream(f"Использую историю нашей с тобой беседы {context}, придумай мне тему для обсуждения"):
            answer = chunk.content.strip()  # Используем атрибут .content

            # Отправляем ответ через WebSocket
            await websocket.send_text(answer)
        

    elif(count == 102):
        print("zashlo")
        for chunk in GigaChat(credentials=api_key,
                              verify_ssl_certs=False,
                                model='GigaChat-2'
                                ).stream(f"Напомни мне пожалуйста вот об этой теме {context}"):
            answer = chunk.content.strip()  # Используем атрибут .content

            # Отправляем ответ через WebSocket
            await websocket.send_text(answer)
    else:
        # Обработка случая, когда не попали ни в одно условие
        print(f"ВНИМАНИЕ: Не найдена подходящая логика обработки!")
        print(f"question_id: {question_id}")
        print(f"count: {count}")
        print(f"should_use_rag: {should_use_rag}")
        print(f"use_rag_for_special: {use_rag_for_special if question_id in [777, 888] else 'N/A'}")
        print(f"retrieval_chain is not None: {retrieval_chain is not None}")
        
        await websocket.send_text("Извините, произошла ошибка при обработке запроса. Попробуйте еще раз.")
            
    await websocket.close()

if __name__ == "__main__":
    print("Запускаем сервер на ws://127.0.0.1:8000/ws")
    uvicorn.run(app, host="0.0.0.0", port=8000)

class DatabaseOperations:
    def __init__(self, db_path=DATABASE_URL):
        self.db_path = db_path

    # Пользователи
    def get_all_users(self):
        """Получение всех пользователей с их статистикой"""
        query = """
        SELECT u.*, 
               COUNT(DISTINCT m.message) as message_count,
               MAX(m.time) as last_activity
        FROM Users u
        LEFT JOIN Message_history m ON u.user_id = m.user_id
        GROUP BY u.user_id
        """
        # Реализация запроса

    # Промпты
    def get_all_prompts(self):
        """Получение всех промптов"""
        query = "SELECT * FROM Prompts ORDER BY created_at DESC"
        # Реализация запроса

    def add_prompt(self, question_text, prompt_template):
        """Добавление нового промпта"""
        query = """
        INSERT INTO Prompts (question_text, prompt_template)
        VALUES (?, ?)
        """
        # Реализация запроса

    def update_prompt(self, question_id, question_text, prompt_template):
        """Обновление промпта"""
        query = """
        UPDATE Prompts 
        SET question_text = ?, prompt_template = ?
        WHERE question_id = ?
        """
        # Реализация запроса

    def delete_prompt(self, question_id):
        """Удаление промпта"""
        query = "DELETE FROM Prompts WHERE question_id = ?"
        # Реализация запроса

    # История сообщений
    def get_user_messages(self, user_id):
        """Получение истории сообщений пользователя"""
        query = """
        SELECT * FROM Message_history 
        WHERE user_id = ? 
        ORDER BY time DESC
        """
        # Реализация запроса

class RAGDocumentManager:
    def __init__(self, base_path=None):
        """
        Инициализирует менеджер документов RAG для новой архитектуры с .md файлами
        Args:
            base_path: Базовый путь к папке с документами (если не указан, используется docs/)
        """
        if base_path is None:
            # Используем новый путь к docs/ по умолчанию
            self.base_path = os.path.join(os.path.dirname(__file__), "docs")
        else:
            self.base_path = base_path
            
        # Новая структура пакетов документов
        self.packs = {
            "competency_lead": os.path.join(self.base_path, "Competency_Lead"),
            "intern": os.path.join(self.base_path, "Intern"),
            "specialist": os.path.join(self.base_path, "Specialist"),
            "po": os.path.join(self.base_path, "PO"),
            "full": os.path.join(self.base_path, "full")
        }

    def get_all_documents(self):
        """Получение списка всех документов по всем пакетам (рекурсивно для .md файлов)"""
        documents = {}
        for pack_name, pack_path in self.packs.items():
            documents[pack_name] = []
            if os.path.exists(pack_path):
                # Рекурсивно собираем все .md файлы
                for root, dirs, files in os.walk(pack_path):
                    md_files = [f for f in files if f.endswith('.md')]
                    for md_file in md_files:
                        # Добавляем относительный путь для лучшей навигации
                        relative_path = os.path.relpath(os.path.join(root, md_file), pack_path)
                        documents[pack_name].append(relative_path)
        return documents

    def add_document(self, file_content, filename, pack_name):
        """Добавление нового документа в указанный пакет"""
        if pack_name not in self.packs:
            raise ValueError(f"Неверное имя пакета: {pack_name}")
        
        # Убеждаемся, что файл имеет расширение .md
        if not filename.endswith('.md'):
            filename += '.md'
        
        # Создаем директорию если не существует
        pack_path = self.packs[pack_name]
        os.makedirs(pack_path, exist_ok=True)
        
        file_path = os.path.join(pack_path, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        # Также добавляем в полную базу
        full_path = os.path.join(self.packs["full"], filename)
        os.makedirs(self.packs["full"], exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(file_content)

    def delete_document(self, filename, pack_name):
        """Удаление документа из указанного пакета"""
        if pack_name not in self.packs:
            raise ValueError(f"Неверное имя пакета: {pack_name}")
        
        # Поддерживаем относительные пути для вложенных папок
        file_path = os.path.join(self.packs[pack_name], filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Удален файл: {file_path}")
            
        # Также удаляем из полной базы (только имя файла без папки)
        filename_only = os.path.basename(filename)
        full_path = os.path.join(self.packs["full"], filename_only)
        if os.path.exists(full_path):
            os.remove(full_path)
            print(f"Удален файл из полной базы: {full_path}")

    def read_document(self, filename, pack_name):
        """Чтение содержимого документа"""
        if pack_name not in self.packs:
            raise ValueError(f"Неверное имя пакета: {pack_name}")
        
        # Поддерживаем относительные пути для вложенных папок
        file_path = os.path.join(self.packs[pack_name], filename)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Файл не найден: {filename} в пакете {pack_name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def update_document(self, file_content, filename, pack_name):
        """Обновление содержимого документа"""
        if pack_name not in self.packs:
            raise ValueError(f"Неверное имя пакета: {pack_name}")
        
        # Поддерживаем относительные пути для вложенных папок
        file_path = os.path.join(self.packs[pack_name], filename)
        
        # Создаем директории если не существуют
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Обновляем файл
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        # Также обновляем в полной базе (только имя файла без папки)
        filename_only = os.path.basename(filename)
        full_path = os.path.join(self.packs["full"], filename_only)
        os.makedirs(self.packs["full"], exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(file_content)


