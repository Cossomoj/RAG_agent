import os
from dotenv import load_dotenv
import string
import asyncio
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

load_dotenv()
# Инициализация FastAPI
app = FastAPI()

api_key = os.getenv("GIGACHAT_API_KEY")
folder_path = "txt_docs"

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

# Инициализация модели для эмбеддингов
model_name = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
model_kwargs = {'device': 'cpu'}
encode_kwargs = {'normalize_embeddings': False}
embedding = HuggingFaceEmbeddings(
    model_name=model_name,
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

# Создание векторного хранилища
vector_store = FAISS.from_documents(split_docs, embedding=embedding)
embedding_retriever = vector_store.as_retriever(search_kwargs={"k": 5})

# Инициализация модели GigaChat

def create_retrieval_chain_from_folder(role, specialization, prompt_template, embedding_retriever):

    # Заполнение шаблона промпта
    template = string.Template(prompt_template)
    filled_prompt = template.substitute(role=role, specialization=specialization)

    # Создание промпта
    prompt = ChatPromptTemplate.from_template(filled_prompt)

    llm = GigaChat(
    credentials=api_key,
    model='GigaChat-Max',
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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Обрабатывает WebSocket соединение и передает стриминг ответа GigaChat."""
    await websocket.accept()
    question = await websocket.receive_text()
    role = await websocket.receive_text()
    specialization = await websocket.receive_text()
    question_id = await websocket.receive_text()
    question_id = int(question_id)
    print(question)
    print(role)
    print(specialization)
    prompt_template = ""
    if (question_id == 1):
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
    elif (question_id == 2):
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
    elif (question_id == 3):
        prompt_template = '''
        Вы исполняете роль $role, а ваша специализация — $specialization.


        Промпт:
        Ты – эксперт по составлению требований и описанию ролей для IT-специалистов. Твоя задача – дать четкий и структурированный ответ на вопрос: "Что ожидается от меня в работе как бизнес-системного аналитика?" основываясь на предоставленной базе знаний.
        Определение уровня : Узнай уровень seniority (Junior, Middle, Senior, Lead) пользователя, чтобы адаптировать ответ.
        Структура ответа :
        Харды : Выбери ключевые технические навыки (инструменты, методологии, технологии), которые соответствуют указанному уровню.
        Софты : Опиши важные личностные качества и soft skills, такие как проактивность, многозадачность, умение принимать обратную связь и т.д.
        Роль и обязанности : Объясни, какие конкретные задачи выполняет аналитик на этом уровне (например, анализ требований, создание документации, координация с командой).
        Адаптация под уровень :
        Для Junior : Фокусируйся на обучении, базовых задачах и взаимодействии с командой.
        Для Middle : Подчеркни увеличение ответственности, использование продвинутых инструментов и участие в сложных проектах.
        Для Senior/Lead : Акцентируй внимание на стратегическом мышлении, лидерстве, влиянии на архитектуру проекта и развитии команды.
        Формат вывода :
        Используй чёткую структуру с разделами: Харды, Софты, Роль и обязанности.
        Добавь примеры реальных ситуаций, где данные навыки могут быть применены.
        Пример ответа для запроса:
        Если пользователь указал уровень Junior :
        Харды : JSON, Postman, User Story, Use Case.
        Софты : Желание учиться, проактивность, способность эффективно переключаться между задачами.
        Роль и обязанности : Анализ требований заказчика, создание простой документации, взаимодействие с командой разработчиков.
        Твой ответ не должен превысить 4096 символов.

        Контекст: {context}
        Вопрос: {input}
        Ответ:
        '''
    elif(question_id == 777):
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

    print(f"📩 Получен запрос: {question}")

    retrieval_chain = create_retrieval_chain_from_folder(role, specialization, prompt_template, embedding_retriever)

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
    
    await websocket.close()

if __name__ == "__main__":
    import uvicorn
    print("Запускаем сервер на ws://127.0.0.1:8000/ws")
    uvicorn.run(app, host="0.0.0.0", port=8000)
