import os
from dotenv import load_dotenv
import string
import asyncio
import sqlite3
from fastapi import FastAPI, WebSocket
import websockets
from langchain_community.document_loaders import TextLoader
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
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
# Инициализация FastAPI
app = FastAPI()

api_key = os.getenv("GIGACHAT_API_KEY")

folder_path_1 = os.path.join(os.path.dirname(__file__), "txt_docs/docs_pack_1")
folder_path_2 = os.path.join(os.path.dirname(__file__), "txt_docs/docs_pack_2")
folder_path_3 = os.path.join(os.path.dirname(__file__), "txt_docs/docs_pack_3")

folder_path_full = os.path.join(os.path.dirname(__file__), "txt_docs/docs_pack_full")

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
        chunk_size=500,  # Размер чанка
        chunk_overlap=100  # Перекрытие между чанками
    )
    split_docs = text_splitter.split_documents(docs)
    return split_docs

# Документы по Специалисту аналитику
split_docs_1 = create_docs_from_txt(folder_path_1)
# Документы по Лиду аналитику
split_docs_2 = create_docs_from_txt(folder_path_2)
# Документы по PO/PM
split_docs_3 = create_docs_from_txt(folder_path_3)
# Полный пакет
split_docs_full = create_docs_from_txt(folder_path_full)

# Инициализация модели для эмбеддингов
model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': False}
embedding = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

# Создание векторного хранилища 1
vector_store_1 = FAISS.from_documents(split_docs_1, embedding=embedding)
embedding_retriever_1 = vector_store_1.as_retriever(search_kwargs={"k": 5})

# Создание векторного хранилища 2
vector_store_2 = FAISS.from_documents(split_docs_2, embedding=embedding)
embedding_retriever_2 = vector_store_2.as_retriever(search_kwargs={"k": 5})

# Создание векторного хранилища 3
vector_store_3 = FAISS.from_documents(split_docs_3, embedding=embedding)
embedding_retriever_3 = vector_store_3.as_retriever(search_kwargs={"k": 5})

# Создание векторного хранилища со всеми данными
vector_store_full = FAISS.from_documents(split_docs_full, embedding=embedding)
embedding_retriever_full = vector_store_full.as_retriever(search_kwargs={"k": 5})


# Инициализация модели GigaChat

def create_retrieval_chain_from_folder(role, specialization, question_id, embedding_retriever, prompt_template):
    
    # Заполнение шаблона промпта
    template = string.Template(prompt_template)
    filled_prompt = template.substitute(role=role, specialization=specialization)

    # Создание промпта
    prompt = ChatPromptTemplate.from_template(filled_prompt)

    llm = GigaChat(
        credentials=api_key,
        model='GigaChat',
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
    """Получает промт из базы данных по ID вопроса"""
    conn = sqlite3.connect('AI_agent.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT prompt_template FROM Prompts WHERE question_id = ?", (question_id,))
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            return None
    finally:
        conn.close()

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
    prompt_template = get_prompt_from_db(question_id)
    if not prompt_template:
        await websocket.send_text("Ошибка: Промт не найден в базе данных")
        return
    
    # Выбираем соответствующий retriever в зависимости от question_id
    embedding_retriever = embedding_retriever_full
    if question_id in [1, 2, 3]:
        embedding_retriever = embedding_retriever_1
    elif question_id in [4, 5, 6, 7, 8, 9, 10, 11, 12, 13]:
        embedding_retriever = embedding_retriever_2
    elif question_id in [14, 15, 16, 17, 18, 19, 20]:
        embedding_retriever = embedding_retriever_3

    retrieval_chain = create_retrieval_chain_from_folder(
        role=role,
        specialization=specialization,
        question_id=question_id,
        embedding_retriever=embedding_retriever,
        prompt_template=prompt_template
    )
    unwanted_chars = ["*", "**"]
    if (count == 1):
        async for chunk in retrieval_chain.astream({'input': question}):
            if chunk:
                    # Извлекаем ответ
                answer = chunk.get("answer", "").strip()

                    # Заменяем ненужные символы
                for char in unwanted_chars:
                    answer = answer.replace(char, " ")
                    
                answer = " ".join(answer.split())  # Удаляем лишние пробелы
                    
                await websocket.send_text(answer)  # Отправляем очищенный текстовый ответ

    elif(count > 1 and count < 10):
        for chunk in GigaChat(credentials=api_key,
                              verify_ssl_certs=False,
                                model='GigaChat-Max'
                                ).stream(f"Использую контекст нашей прошлой беседы {context}, ответь на уточняющий вопрос {question}"):
            answer = chunk.content.strip()  # Используем атрибут .content

            # Заменяем ненужные символы
            for char in unwanted_chars:
                answer = answer.replace(char, " ")

            # Удаляем лишние пробелы
            answer = " ".join(answer.split())

            # Отправляем ответ через WebSocket
            await websocket.send_text(answer)

    elif(count == 102):
        for chunk in GigaChat(credentials=api_key,
                              verify_ssl_certs=False,
                                model='GigaChat'
                                ).stream(f"Напомни мне пожалуйста вот об этой теме {context}"):
            answer = chunk.content.strip()  # Используем атрибут .content

            # Заменяем ненужные символы
            for char in unwanted_chars:
                answer = answer.replace(char, " ")

            # Удаляем лишние пробелы
            answer = " ".join(answer.split())

            # Отправляем ответ через WebSocket
            await websocket.send_text(answer)
            
    await websocket.close()

if __name__ == "__main__":
    print("Запускаем сервер на ws://127.0.0.1:8000/ws")
    uvicorn.run(app, host="0.0.0.0", port=8000)
