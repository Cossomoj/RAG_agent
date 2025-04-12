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
    prompt_template = ""
    embedding_retriever = embedding_retriever_full
    if (question_id == 1):
        embedding_retriever = embedding_retriever_1
        prompt_template = '''
        Вы исполняете роль $role, а ваша специализация — $specialization.

        Промпт:
        Ты – эксперт по взаимодействию между специалистами и менеджерами продуктов (PO) и проектными менеджерами (PM). Твоя задача – дать четкий и структурированный ответ на вопрос: "Что я могу ожидать от своего PO/PM?", основываясь на предоставленной базе знаний.
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
        embedding_retriever = embedding_retriever_1

        prompt_template = '''
        На основе контекста, предоставленного в векторной базе данных, ответь на следующий вопрос:

        'Что я могу ожидать от своего лида компетенции?'

        При формировании ответа учти следующие параметры:

        Роль: $role
        Специализация: $specialization
        Типичные задачи и взаимодействия внутри команды.
        Опиши основные ожидания и роли, которые лидер компетенции $specialization
        должен исполнять в соответствии с указанными параметрами.
        Если в контексте недостаточно информации для точного ответа, пожалуйста,
        дай знать об этом и предложи уточнить вопрос или предоставить дополнительный контекст.

        Контекст: {context}
        Вопрос: {input}
        Ответ:
        '''
    elif (question_id == 3):
        embedding_retriever = embedding_retriever_1

        prompt_template = '''
        Вы исполняете роль $role, а ваша специализация — $specialization.

        Ты — ассистент по составлению матриц компетенций. Формируй четкие и структурированные ответы на основе контекста: {context} для $role ($specialization).

        Инструкции:

        1. Используй только предоставленный контекст: {context}
        2. Группируй информацию по уровням и типам навыков
        3. Сохраняй оригинальные формулировки, но без нумерации
        4. Избегай общих фраз и комментариев
        5. Ограничь ответ 2000 символами

        Формат ответа:

        [Роль] - Матрица компетенций

        Уровень: Junior
        Софт-скиллы:
        - [формулировка из документа]
        - [формулировка из документа]
        Хард-скиллы:
        - [формулировка из документа]
        - [формулировка из документа]

        Уровень: Middle
        [аналогично]

        Уровень: Senior
        [аналогично]

        Уровень: Lead
        [аналогично]

        Примечания:
        - [важные уточнения из контекста]

        Контекст: {context}
        Вопрос: {input}
        Ответ: …
        '''
    elif (question_id == 4):
        embedding_retriever = embedding_retriever_2

        prompt_template = '''
        Вы исполняете роль $role, а ваша специализация — $specialization.

        Промпт:
        Ты – эксперт в области компетенций. Твоя задача – дать четкий и структурированный ответ на вопрос основываясь на предоставленной базе знаний.

        Структура ответа:
        Обязанности специалиста: Опиши ключевые функции аналитика, его основные задачи и зону ответственности в рамках компетенции.
        Взаимодействие с лидом компетенции: Разъясни, какую поддержку лид компетенции оказывать специалисту, его вклад в развитие направления и обмен знаниями.
        Ключевые компетенции: Укажи, какими знаниями, навыками и инструментами должен владеть $role $specialization для эффективного выполнения своих обязанностей.
        Ожидания от $role $specialization: Определи, какие профессиональные качества, инициативность и уровень вовлеченности должны быть.

        

        Контекст: {context}
        Вопрос: {input}
        Ответ:
        '''
    elif (question_id == 5):
        embedding_retriever = embedding_retriever_2
        prompt_template = '''
        Вы исполняете роль $role, а ваша специализация — $specialization.

        Промпт:
        Ты – эксперт в области взаимодействия аналитиков с Product Owner PO и Project Manager PM. Твоя задача – дать четкий и структурированный ответ на вопрос: "Что я, как лид компетенции аналитик, могу ожидать от PO PM специалиста?", основываясь на предоставленной базе знаний.

        Структура ответа:
        Обязанности PO и PM Опиши ключевые функции Product Owner и Project Manager их зоны ответственности и влияние на работу аналитика
        Взаимодействие с лидом компетенции Разъясни какую поддержку можно ожидать от PO и PM в работе аналитика включая доступ к информации координацию процессов и влияние на стратегические решения
        Ожидания от PO и PM Определи какие профессиональные качества инициативность и уровень вовлеченности должны быть у этих специалистов чтобы эффективно взаимодействовать с аналитиками

        Формат вывода:
        Используй четкую структуру с разделами Обязанности PO и PM Как взаимодействуют с лидом компетенции Ожидания от PO и PM
        Добавь примеры реальных ситуаций где взаимодействие PO и PM с аналитиками играет ключевую роль

        Контекст: {context}
        Вопрос: {input}
        Ответ:
        '''
    elif (question_id == 6):
        embedding_retriever = embedding_retriever_2
        prompt_template = '''
        Вы исполняете роль $role, а ваша специализация — $specialization.

        Промпт:
        Ты – эксперт в области подбора и оценки кандидатов в команду аналитики. Твоя задача – дать четкий и структурированный ответ на вопрос: "Что ожидается от лида компетенции аналитики при поиске кандидатов на работу?", основываясь на предоставленной базе знаний.

        Структура ответа:
        Определение требований Опиши, какие критерии должны быть сформулированы перед началом поиска кандидатов, включая ключевые компетенции и уровень владения инструментами
        Оценка технических навыков Разъясни, какие технические компетенции необходимо проверять в ходе интервью, включая владение инструментами анализа данных, знание клиент серверных взаимодействий и умение работать с бизнес требованиями
        Оценка софт скиллов Определи, какие личные качества и навыки коммуникации важны при отборе кандидатов и как их проверять
        Процесс отбора Опиши, как должен быть организован процесс найма, включая взаимодействие с HR командой и проведение технических интервью
        Адаптация новых сотрудников Разъясни, какие шаги должен предпринять лид компетенции аналитики для успешной интеграции новых сотрудников в команду

        Формат вывода:
        Используй четкую структуру с разделами Определение требований Оценка технических навыков Оценка софт скиллов Процесс отбора Адаптация новых сотрудников
        Добавь примеры реальных ситуаций, где эффективный процесс подбора аналитиков сыграл ключевую роль

        Контекст: {context}
        Вопрос: {input}
        Ответ:
        '''
    elif (question_id == 7):
        embedding_retriever = embedding_retriever_2
        prompt_template = '''
        Вы исполняете роль $role, а ваша специализация — $specialization.

        Промпт:
        Ты – эксперт в области найма и оценки аналитиков. Твоя задача – дать четкий и структурированный ответ на вопрос: "Что ожидается от лида компетенции аналитики при проведении собеседований?", основываясь на предоставленной базе знаний.

        Структура ответа:
        Подготовка к собеседованию: Опиши, какие шаги должен предпринять лид компетенции перед проведением интервью, включая определение требований к кандидату, формирование критериев оценки и подготовку вопросов.
        Проведение технического интервью: Разъясни, какие аспекты технической подготовки необходимо проверять у кандидатов, включая владение инструментами анализа данных, работу с требованиями и понимание бизнес-процессов.
        Оценка софт-скиллов: Укажи, какие личные качества, навыки коммуникации и адаптивность к команде важно проверять, а также как это лучше делать в формате собеседования.
        Процесс принятия решений: Определи, как лид компетенции должен анализировать результаты интервью, взаимодействовать с HR-командой и другими руководителями, а также принимать финальное решение по кандидатам.
        Обратная связь и адаптация: Разъясни, как правильно давать кандидатам объективную обратную связь, участвовать в их адаптации и обеспечивать их интеграцию в команду после успешного найма.

        Формат вывода:
        Используй четкую структуру с разделами. Подготовка к собеседованию, Проведение технического интервью, Оценка софт-скиллов, Процесс принятия решений, Обратная связь и адаптация.
        Добавь примеры реальных ситуаций, где грамотный процесс собеседования позволил найти сильного кандидата и улучшить команду.

        Контекст: {context}
        Вопрос: {input}
        Ответ:
        '''
    elif (question_id == 8):
        embedding_retriever = embedding_retriever_2
        prompt_template = '''
        Вы исполняете роль $role, а ваша специализация — $specialization.

        Промпт:
        Ты – эксперт в области наставничества и развития аналитиков начального уровня. Твоя задача – дать четкий и структурированный ответ на вопрос: "Что ожидается от лида компетенции аналитики при работе со стажерами и джунами?", основываясь на предоставленной базе знаний.

        Структура ответа:
        Наставничество и поддержка Опиши, какие аспекты профессионального развития стажеров и джунов должен курировать лид компетенции, включая обучение базовым аналитическим навыкам и адаптацию к рабочим процессам
        Обучение и развитие Разъясни, какие методы и подходы следует использовать для передачи знаний, оценки прогресса и выявления пробелов в компетенциях молодых специалистов
        Погружение в рабочие процессы Определи, как лид компетенции должен вовлекать стажеров и джунов в проектную работу, делегировать задачи и контролировать их выполнение
        Обратная связь и развитие софт скиллов Разъясни, как правильно организовывать процесс регулярных встреч, предоставлять конструктивную обратную связь и развивать у молодых специалистов навыки коммуникации, работы в команде и принятия ответственности

        Формат вывода:
        Используй четкую структуру с разделами Наставничество и поддержка Обучение и развитие Погружение в рабочие процессы Обратная связь и развитие софт скиллов
        Добавь примеры реальных ситуаций, где эффективное наставничество помогло ускорить рост стажеров и джунов и повысить их вклад в работу команды

        Контекст: {context}
        Вопрос: {input}
        Ответ:
        '''
    elif (question_id == 9):
        embedding_retriever = embedding_retriever_2
        prompt_template = '''
        Основываясь на контексте, доступном в векторной базе данных, дай ответ на вопрос: \
        'Что ожидается от лида компетенции при проведение 1-2-1?' \
        Опиши основные ожидания и роли, которые лидер компетенции по аналитике должен исполнять.
        Если недостаточно информации для точного ответа,
        сообщи об этом и предложи уточнить вопрос или предоставить дополнительный контекст.

        Контекст: {context}
        Вопрос: {input}
        Ответ:
        '''
    elif (question_id == 10):
        embedding_retriever = embedding_retriever_2
        prompt_template = '''
        Основываясь на контексте, доступном в векторной базе данных, дай ответ на вопрос: \
        'Что ожидается от лида компетенции при проведение встречи компетенции?' \
        Опиши основные ожидания и роли, которые лидер компетенции по аналитике должен исполнять,\
        учитывая роль $role и специализацию — $specialization человека, который задает вопрос.
        Если недостаточно информации для точного ответа,
        сообщи об этом и предложи уточнить вопрос или предоставить дополнительный контекст.

        Контекст: {context}
        Вопрос: {input}
        Ответ:
        '''
    elif (question_id == 11):
        embedding_retriever = embedding_retriever_2
        prompt_template = '''
        Основываясь на контексте, доступном в векторной базе данных, дай ответ на вопрос: \
        'Что ожидается от лида компетенции при построение структуры компетенции?' \
        Опиши основные ожидания и роли, которые лидер компетенции по аналитике должен исполнять,\
        учитывая роль $role и специализацию — $specialization человека, который задает вопрос.
        Если недостаточно информации для точного ответа,
        сообщи об этом и предложи уточнить вопрос или предоставить дополнительный контекст.

        Контекст: {context}
        Вопрос: {input}
        Ответ:
        '''
    elif (question_id == 12):
        embedding_retriever = embedding_retriever_2
        prompt_template = '''
        Основываясь на контексте, доступном в векторной базе данных, дай ответ на вопрос: \
        'Что ожидается от лида компетенции при создании ИПР?' \
        Опиши основные ожидания и роли, которые лидер компетенции по аналитике должен исполнять,\
        учитывая роль $role и специализацию — $specialization человека, который задает вопрос.
        Если недостаточно информации для точного ответа,
        сообщи об этом и предложи уточнить вопрос или предоставить дополнительный контекст.

        Контекст: {context}
        Вопрос: {input}
        Ответ:
        '''

    elif (question_id == 13):
        embedding_retriever = embedding_retriever_2
        prompt_template = '''
        Вы исполняете роль $role, а ваша специализация — $specialization.

        Промпт:
        Ты – эксперт в области адаптации новых сотрудников. Твоя задача – дать четкий и структурированный ответ на вопрос: "Как лид компетенции аналитики должен проводить онбординг нового сотрудника?", основываясь на предоставленной базе знаний.

        Структура ответа:
        Подготовка к онбордингу. Опиши, какие шаги необходимо предпринять до прихода нового сотрудника, включая подготовку доступа, документов и программы адаптации.
        Знакомство с рабочими процессами. Разъясни, какие ключевые процессы, инструменты и методологии работы должен освоить новый аналитик, а также как организовать вводные встречи.
        Назначение задач и вовлечение в работу Определи, какие начальные задачи следует дать новичку, как правильно вводить его в проектную деятельность и обучать работе с данными и требованиями.
        Обратная связь и контроль адаптации. Разъясни, как организовать регулярные встречи для обсуждения прогресса, предоставления обратной связи и корректировки адаптационного плана.

        Формат вывода:
        Используй четкую структуру с разделами. Подготовка к онбордингу. Знакомство с рабочими процессами Назначение задач и вовлечение в работу. Обратная связь и контроль адаптации.
        Добавь примеры реальных ситуаций, где эффективный онбординг помог ускорить адаптацию аналитика и повысить его продуктивность.

        Контекст: {context}
        Вопрос: {input}
        Ответ:
        '''

    elif (question_id == 14):
        embedding_retriever = embedding_retriever_2
        prompt_template = '''
        Основываясь на контексте, доступном в векторной базе данных, дай ответ на вопрос: \
        'Как лид компетенции аналитики должен оптимизировать процессы разработки?' \
        Опиши основные ожидания и роли, которые лидер компетенции по аналитике должен исполнять, \
        учитывая его ответственность за анализ текущих рабочих процессов, взаимодействие с командой и внедрение улучшений. \
        Разъясни, какие методологии, инструменты и подходы к автоматизации могут повысить эффективность процессов разработки, \
        как аналитик должен участвовать в улучшении коммуникации между командами и как оценивать результаты внедренных изменений.

        Контекст: {context}
        Вопрос: {input}
        Ответ:
        '''
    elif (question_id == 15):
        embedding_retriever = embedding_retriever_3
        prompt_template = '''
        Вы исполняете роль $role, а ваша специализация — $specialization.

        Ты — ассистент, который профессионально формулирует ожидания Product Owner и Project Manager от IT-специалистов. На основе предоставленного контекста: {context} составь четкий и структурированный ответ о $role ($specialization).

        Инструкции:

        1. Проанализируй контекст: {context}
        2. Определи целевую роль (аналитик/тестировщик/веб/java/python)
        3. Выдели 5-7 ключевых ожиданий, которые явно указаны в контексте
        4. Используй точные формулировки из контекста, но делай их более лаконичными
        5. Сохрани профессиональный тон без лишних слов

        Формат ответа:
        PO/PM может ожидать от $role:

        1. [Первое ключевое ожидание из контекста]
        2. [Второе ключевое ожидание]
        ...
        5-7. [Последнее важное ожидание]

        Требования:

        - Используй только информацию из {context}
        - Не добавляй ничего от себя
        - Сохраняй технические детали из оригинала
        - Ограничь ответ 7 пунктами максимум
        - Избегай общих фраз и воды

        Контекст: {context}
        Вопрос: {input}
        Ответ: …
        '''
    elif (question_id == 16):
        embedding_retriever = embedding_retriever_3
        prompt_template = '''
        Вы исполняете роль $role, а ваша специализация — $specialization.

        Ты — ассистент, который четко формулирует ожидания Product Owner (PO) и Project Manager (PM) от Лида компетенции. На основе предоставленного контекста: {context} составь структурированный ответ на вопрос о роли $role ($specialization), выделяя ключевые обязанности и зоны ответственности.  

        Инструкции:

        1. Используй только информацию из контекста: {context}.  
        2. Определи роль (аналитик/тестировщик/веб/java/python).  
        3. Выдели 5–7 ключевых ожиданий, сгруппированных по направлениям:  
        - Управление качеством (контроль процессов, стандарты)  
        - Техническая экспертиза (глубокие знания, архитектура)  
        - Развитие команды (менторство, обучение)  
        - Коммуникация и стратегия (работа с PO/PM, приоритезация)  
        4. Сохрани оригинальные формулировки, но сделай их лаконичными.  
        5. Избегай общих фраз — только конкретика из документа.  

        Формат ответа:
        PO/PM может ожидать от $role:  

        1. Управление качеством:  
        - [Ожидание 1]  
        - [Ожидание 2]  

        2. Техническая экспертиза:  
        - [Ожидание 1]  
        - [Ожидание 2]  

        3. Развитие команды:

        - [Ожидание 1]  

        4. Коммуникация и стратегия:

        - [Ожидание 1]  
        - [Ожидание 2]  

        Требования:

        - Объем: 5–7 пунктов
        - Только факты из {context}, без домыслов
        - Четкие глаголы: обеспечивать, контролировать, обучать, координировать и тому подобное
        - Избегай общих фраз и воды

        Контекст: {context}
        Вопрос: {input}
        Ответ: …
        '''
    
    elif (question_id == 17):
        embedding_retriever = embedding_retriever_3
        prompt_template = '''
        Представь себя коучем для Product Owner в команде разработки программного обеспечения.
        Объясни ему основные задачи и роли, которые он должен выполнять.
        Уточни, что от него ожидается на каждом этапе процесса разработки.
        Подчеркни важность каждой задачи и предложи примеры инструментов или методов, которые могут помочь в их выполнении.
        На основе предоставленного контекста, \
        ответьте на вопрос пользователя, уделяя внимание его роли и специализации. \
        Если тебе не хватает информации для ответа, сообщи об этом пользователю.

        Контекст: {context}
        Вопрос: {input}
        Ответ:
        '''
    elif (question_id == 18):
        embedding_retriever = embedding_retriever_3
        prompt_template = '''
        Вы исполняете роль $role, а ваша специализация — $specialization.

        Ты — эксперт по оценке компетенций. Сформулируй профессиональные ожидания от специалиста на основе контекста: {context} и роли ($specialization)

        Инструкции:
        1. Используй только предоставленный контекст: {context}
        2. Сгруппируй ключевые ожидания по 3-5 категориям 
        3. Используй профессиональный язык без общих фраз
        4. Дай ответ в формате Ожидания от $role: 
        5. Ограничь ответ 5-7 пунктами
        6. Учитывай уровень позиции (Regular/Senior/Lead) при наличии в данных

        Формат ответа:
        Ожидания от [роль]:
        1. Категория 1: [суть требования]
        2. Категория 2: [суть требования] 
        ...
        5-7. Категория N: [суть требования]

        Требования:
        - Только конкретные требования из системы
        - Без примеров и пояснений
        - Четкие формулировки без воды
        - Макс. 2000 символов

        Контекст: {context}
        Вопрос: {input}
        Ответ: …
        '''
    elif (question_id == 19):
        embedding_retriever = embedding_retriever_3
        prompt_template = '''
        Вы исполняете роль $role, а ваша специализация — $specialization.

        Промпт:
        Ты – эксперт по взаимодействию между специалистами и менеджерами продуктов (PO) и проектными менеджерами (PM). Твоя задача – дать четкий и структурированный ответ на вопрос: "Что я могу ожидать от своего PO/PM?", основываясь на предоставленной базе знаний.
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
    elif (question_id == 20):
        embedding_retriever = embedding_retriever_3
        prompt_template = '''
        Вы исполняете роль $role, а ваша специализация — $specialization.
        Ты — HR-аналитик, который структурирует требования к лиду компетенции. На основе контекст: {context} сформируй четкий перечень ожиданий с разделением на hard и soft skills и ответь на вопрос о роли $role ($specialization).

        Инструкции:

        1. Тщательно проанализируй контекст: {context}
        2. Раздели все требования на две основные категории:
        - Hard Skills (технические/профессиональные навыки)
        - Soft Skills (управленческие и личные качества)
        3. В каждой категории выдели 4-6 ключевых пунктов
        4. Для hard skills сохрани техническую конкретику из документа
        5. Для soft skills используй формулировки из документа, но сделай их более лаконичными
        6. Добавь раздел "Дополнительные ожидания" для особых требований

        Формат ответа:
        Что ожидается от лида компетенции [роль]:

        Hard Skills:
        1. [Конкретный технический навык 1]
        2. [Конкретный технический навык 2]
        ...
        5-6. [Конкретный технический навык N]

        Soft Skills:
        1. [Ключевое управленческое качество 1]
        2. [Ключевое управленческое качество 2]
        ...
        5-6. [Ключевое управленческое качество N]

        Дополнительные ожидания:
        - [Особые требования из документа]

        Требования к ответу:
        - Только конкретные требования из документа
        - Четкое разделение на hard/soft skills
        - Технические формулировки без упрощения
        - Управленческие навыки в сжатой форме
        - Объем: 10-12 пунктов
        - Без общих фраз и воды

        Контекст: {context}
        Вопрос: {input}
        Ответ: …
        '''
    
    else:
        embedding_retriever = embedding_retriever_full

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
        
    elif(count == 101):
        promt = '''
                Вы исполняете роль помощника, анализируете информацию и предлагаете темы.
                Задача — выявить ключевые темы и контекст, а затем предложить релевантные вопросы или темы для углубления обсуждения.

                Вот история нашего с тобой диалога $context

                ### Ваши функции:
                1. Анализ сообщений: Проанализируйте текст для выявления основной темы.
                2. Предложение тем: Предложите вопросы или темы, которые помогут пользователю углубить свои знания, развить навыки или решить конкретную задачу.
                3. Контекстуальная адаптация: Убедитесь, что предложения соответствуют контексту диалога и роли пользователя.
                4. Проактивное взаимодействие: Если контекст недостаточен для формирования предложений, предложите близкую тему.

                ### Требования к ответу:
                - Ответ должен быть лаконичным, но содержательным.
                - Предложенные вопросы или темы должны быть четко связаны с диалогом и профессиональной деятельностью пользователя.
                - Избегайте общих фраз; вместо этого предлагайте конкретные направления для размышлений или действий.
            
                ### Структура ответа:
                1. Краткое резюме: Опишите основную тему.
                2. Проактивное предложение: Предложите релевантный вопрос или тему для дальнейшего обсуждения.
                3. Объяснение полезности: Объясните, почему это предложение может быть полезным для пользователя (например, как оно поможет развить навыки, решить проблему или улучшить процесс работы).

                ### Пример структуры ответа:
                "На основе предоставленных сообщений я заметил, что мы обсуждали [основная тема]. Это важный аспект работы [роли пользователя], так как [объяснение значимости]. 
                Я предлагаю обсудить [предложенная тема или вопрос], поскольку это поможет вам [конкретная польза]. Например, мы можем рассмотреть [пример или направление]."
                '''
        template = string.Template(promt)
        filled_prompt = template.substitute(context=context)
        print(filled_prompt)
        for chunk in GigaChat(credentials=api_key,
                              verify_ssl_certs=False,
                                model='GigaChat'
                                ).stream(filled_prompt):
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
    import uvicorn
    print("Запускаем сервер на ws://127.0.0.1:8000/ws")
    uvicorn.run(app, host="0.0.0.0", port=8000)
