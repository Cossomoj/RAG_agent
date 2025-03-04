import os
from dotenv import load_dotenv
import string
import asyncio
import pickle
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
from collections import defaultdict

# Загрузка переменных окружения
load_dotenv()

# Инициализация FastAPI
app = FastAPI()

api_key = os.getenv("GIGACHAT_API_KEY")
folder_path = os.path.join(os.path.dirname(__file__), "txt_docs")

# Инициализация модели для эмбеддингов
model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': False}
embedding = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

# Маппинг ролей (фронт -> бэкенд)
ROLE_MAPPING = {
    "Бизнес-PO/PM": "role_PM",
    "Лид компетенций": "role_lead",
    "Специалист": "role_employee"
}

# Загрузка документов
def load_documents(folder_path):
    file_paths = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".txt")]
    docs = []
    for file_path in file_paths:
        loader = TextLoader(file_path)
        docs.extend(loader.load())
    return docs

# Разделение документов по ролям
def split_documents_by_role(docs):
    role_to_docs = defaultdict(list)
    for doc in docs:
        if "role_PM" in doc.metadata.get("source", ""):
            role_to_docs["PM"].append(doc)
        elif "role_employee" in doc.metadata.get("source", ""):
            role_to_docs["role_employee"].append(doc)
        elif "role_lead" in doc.metadata.get("source", ""):
            role_to_docs["role_lead"].append(doc)
        else:
            role_to_docs["other"].append(doc)
    return role_to_docs

# Создание индексов для каждой роли
def create_indexes(role_to_docs, embedding):
    role_to_index = {}
    for role, docs in role_to_docs.items():
        if docs:  # Если есть документы для этой роли
            index_path = f"faiss_index_{role}.index"
            vector_store = FAISS.from_documents(docs, embedding=embedding)
            vector_store.save_local(index_path)
            role_to_index[role] = vector_store
            print(f"Индекс для роли '{role}' создан и сохранен в {index_path}")
    return role_to_index

# Загрузка индексов
def load_indexes(roles, embedding):
    role_to_index = {}
    for role in roles:
        index_path = f"faiss_index_{role}.index"
        if os.path.exists(index_path):
            vector_store = FAISS.load_local(index_path, embedding, allow_dangerous_deserialization=True)
            role_to_index[role] = vector_store
            print(f"Индекс для роли '{role}' загружен из {index_path}")
        else:
            print(f"Индекс для роли '{role}' не найден.")
    return role_to_inde

# Загрузка документов и создание/загрузка индексов
docs = load_documents(folder_path)
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
split_docs = text_splitter.split_documents(docs)
role_to_docs = split_documents_by_role(split_docs)

roles = ["role_PM", "role_employee", "role_lead", "other"]
if not all(os.path.exists(f"faiss_index_{role}.index") for role in roles):
    print("Создаем индексы...")
    role_to_index = create_indexes(role_to_docs, embedding)
else:
    print("Загружаем индексы...")
    role_to_index = load_indexes(roles, embedding)

# Инициализация модели GigaChat
def create_retrieval_chain_from_folder(role, specialization, prompt_template, embedding_retriever):
    template = string.Template(prompt_template)
    filled_prompt = template.substitute(role=role, specialization=specialization)
    prompt = ChatPromptTemplate.from_template(filled_prompt)

    llm = GigaChat(
        credentials=api_key,
        model='GigaChat',
        verify_ssl_certs=False,
        profanity_check=False
    )

    document_chain = create_stuff_documents_chain(llm=llm, prompt=prompt)
    retrieval_chain = create_retrieval_chain(embedding_retriever, document_chain)
    return retrieval_chain

"""@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    Обрабатывает WebSocket соединение и передает стриминг ответа GigaChat.
    await websocket.accept()
    question = await websocket.receive_text()
    role = await websocket.receive_text()
    specialization = await websocket.receive_text()
    question_id = await websocket.receive_text()
    question_id = int(question_id)
    print(question)
    print(role)
    print(specialization)
    prompt_template = """

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Обрабатывает WebSocket соединение и передает стриминг ответа GigaChat."""
    await websocket.accept()
    try:
        # Получаем данные от фронта
        question = await websocket.receive_text()
        role = await websocket.receive_text()  # Роль от фронта
        specialization = await websocket.receive_text()
        question_id = await websocket.receive_text()
        question_id = int(question_id)

        print(f"📩 Получен запрос: {question}")
        print(f"Роль (с фронта): {role}")
        print(f"Специализация: {specialization}")

        # Преобразуем роль из формата фронта в формат бэкенда
        search_role = ROLE_MAPPING.get(role, "other")  # Если роль не найдена, используем "other"
        print(f"🔍 Используем индекс для роли: {search_role}")

        # Выбор шаблона промпта в зависимости от question_id
        if question_id == 1:
            prompt_template = '''
            Вы исполняете роль $role, а ваша специализация — $specialization.

            Промпт:
            Ты – эксперт по взаимодействию между аналитиками и менеджерами продуктов (PO) и проектными менеджерами (PM). Твоя задача – дать четкий и структурированный ответ на вопрос: "Что я могу ожидать от своего PO/PM?", основываясь на предоставленной базе знаний.
            Определение роли:
            Узнай роль пользователя (бизнес-аналитик, системный аналитик, продуктовый аналитик), чтобы адаптировать ответ.

            Структура ответа:
            Обязанности PO/PM: Опиши ключевые функции Product Owner (PO) и Project Manager (PM), их зоны ответственности и влияние на работу аналитика.
            Взаимодействие с аналитиком: Разъясни, какую поддержку можно ожидать от PO/PM в работе аналитика: постановка задач, доступ к информации, координация с командой.
            Ожидания в зависимости от уровня аналитика:

            Для Junior: PO/PM помогает с приоритезацией, обучением, уточнением требований.
            Для Middle: PO/PM ожидает проактивности в анализе, а сам обеспечивает доступ к бизнес-стейкхолдерам.
            Для Senior: PO/PM полагается на аналитика в стратегическом планировании и формировании продуктовой/проектной стратегии.
            Формат вывода:
            Используй четкую структуру с разделами: Обязанности PO/PM, Как взаимодействует с аналитиком, Ожидания в зависимости от уровня.
            Добавь примеры реальных ситуаций, где взаимодействие с PO/PM играет ключевую роль.
            Твой ответ не должен превысить 4096 символов.
            Контекст: {context}
            Вопрос: {input}
            Ответ:
            '''
        elif question_id == 2:
            prompt_template = '''
            На основе контекста, предоставленного в векторной базе данных, ответь на следующий вопрос:

            'Что я могу ожидать от своего лида компетенции?'

            При формировании ответа учти следующие параметры:

            Роль: $role
            Специализация: $specialization
            Типичные задачи и взаимодействия внутри команды.
            Опиши основные ожидания и роли, которые лидер компетенции по аналитике
            должен исполнять в соответствии с указанными параметрами.
            Если в контексте недостаточно информации для точного ответа, пожалуйста,
            дай знать об этом и предложи уточнить вопрос или предоставить дополнительный контекст.
            Твой ответ не должен превысить 4096 символов.

            Контекст: {context}
            Вопрос: {input}
            Ответ:
            '''
        elif question_id == 3:
            prompt_template = '''
            Вы исполняете роль $role, а ваша специализация — $specialization.

            Ты – эксперт по составлению требований и описанию ролей для IT-специалистов.
            Сформулируй структурированный ответ на запрос, связанный с анализом матрицы компетенций для разных уровней специалистов используя данные из контекста.
            Ответ должен быть представлен в виде списка уровней Junior, Junior+/Middle-, Middle+ с разделением на soft skills (софты) и hard skills (харды) для каждого уровня.
            Если вам не хватает информации для ответа, сообщите об этом пользователю, а также предложите уточнить вопрос или предоставить дополнительный контекст.

            Пример ожидаемого формата ответа:

            Уровень Junior
            Софты:
            ...
            ...
            Харды:
            ...
            ...
            Уровень Junior+/Middle-
            Софты:
            ...
            ...
            Харды:
            ...
            ...
            И так далее для других уровней.

            Контекст: {context}
            Вопрос: {input}
            Ответ:
            '''
        elif question_id == 777:
            prompt_template = '''
            Вы исполняете роль $role, а ваша специализация — $specialization.
            Ваши функции включают:

            Решение вопросов, связанных с $specialization, используя данные из контекста.
            Консультирование и предложение рекомендаций, необходимых для выполнения задач в рамках $role.
            Предоставление информации и помощь в решении проблем в контексте $specialization и $role.
            На основе предоставленного контекста, \
            ответьте на вопрос пользователя, уделяя внимание его роли и специализации. \
            Если вам не хватает информации для ответа, сообщите об этом пользователю, \
            а также предложите уточнить вопрос или предоставить дополнительный контекст.
            Твой ответ не должен превысить 4096 символов.

            Контекст: {context}
            Вопрос: {input}
            Ответ:
            '''
        else:
            await websocket.send_text("Неизвестный question_id.")
            await websocket.close()
            return

        # Проверяем, существует ли индекс для этой роли
        if search_role in role_to_index:
            embedding_retriever = role_to_index[search_role].as_retriever(search_kwargs={"k": 5})
        else:
            await websocket.send_text("Роль не найдена в базе данных.")
            await websocket.close()
            return

        # Создаем цепочку для поиска
        retrieval_chain = create_retrieval_chain_from_folder(search_role, specialization, prompt_template, embedding_retriever)

        # Задаем массив лишних символов
        unwanted_chars = ["*", "**"]
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

    except Exception as e:
        print(f"Ошибка: {e}")
        await websocket.send_text(f"Произошла ошибка: {e}")
    finally:
        # Закрываем соединение только после завершения всех операций
        await websocket.close()
    
if __name__ == "__main__":
    import uvicorn
    print("Запускаем сервер на ws://127.0.0.1:8000/ws")
    uvicorn.run(app, host="0.0.0.0", port=8000)