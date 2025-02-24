import os
import asyncio
from fastapi import FastAPI, WebSocket
import websockets
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

# Инициализация FastAPI
app = FastAPI()


# Загрузите PDF-файл
pdf_folder = 'pdf_docs'

# Получаем список всех PDF-файлов в папке
pdf_files = [os.path.join(pdf_folder, f) for f in os.listdir(pdf_folder) if f.endswith('.pdf')]

# Загружаем все PDF-файлы
docs = []
for pdf_path in pdf_files:
    loader = PyPDFLoader(pdf_path)
    docs.extend(loader.load())

# Разделите текст на чанки
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,  # Размер чанка
    chunk_overlap=100  # Перекрытие между чанками
)
split_docs = text_splitter.split_documents(docs)

model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': False}
embedding = HuggingFaceEmbeddings(model_name=model_name,
                                  model_kwargs=model_kwargs,
                                  encode_kwargs=encode_kwargs)

vector_store = FAISS.from_documents(split_docs, embedding=embedding)
embedding_retriever = vector_store.as_retriever(search_kwargs={"k": 5})

auth = "YTU3OTBkMzktYzA4OS00MmM2LTllYWUtNWE5Nzg5OGQyOGU4OjkxNWU1MmRkLWMwMGYtNGU3ZC04OGIwLWY4NjE4OTYyM2FkZA=="
llm = GigaChat(credentials=auth,
              model='GigaChat:latest',
               verify_ssl_certs=False,
               profanity_check=False,
               streaming=True)

prompt = ChatPromptTemplate.from_template('''Ответь на вопрос пользователя. \
Используй при этом только информацию из контекста. Если в контексте нет \
информации для ответа, сообщи об этом пользователю.
Контекст: {context}
Вопрос: {input}
Ответ:'''
)
document_chain = create_stuff_documents_chain(
    llm=llm,
    prompt=prompt
    )
retrieval_chain = create_retrieval_chain(embedding_retriever, document_chain)


"""q1 = 'Компетенции системного аналитика уровня junior'
resp1 = retrieval_chain.invoke(
    {'input': q1}
)
print(resp1)"""

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Обрабатывает WebSocket соединение и передает стриминг ответа GigaChat."""
    await websocket.accept()
    question = await websocket.receive_text()
    print(f"📩 Получен запрос: {question}")

    # Задаем массив лишних символов
    unwanted_chars = ["\n", "*", "**"]

    # Запускаем стриминг ответа
    async for chunk in retrieval_chain.astream({'input': question}):
        if chunk:
            # Извлекаем ответ
            answer = chunk.get("answer", "").strip()

            # Заменяем ненужные символы
            for char in unwanted_chars:
                answer = answer.replace(char, " ")

            answer = " ".join(answer.split())  # Удаляем лишние пробелы
            
            await websocket.send_text(answer)  # Отправляем очищенный текстовый ответ
    
    await websocket.close()

if __name__ == "__main__":
    import uvicorn
    print("Запускаем сервер на ws://127.0.0.1:8000/ws")
    uvicorn.run(app, host="0.0.0.0", port=8000)
