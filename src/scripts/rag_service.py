import string
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_gigachat import GigaChat
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain.retrievers import EnsembleRetriever

# Укажите путь к вашему PDF-файлу
pdf_path = "test_file.pdf"

# Загрузите PDF-файл
loader = PyPDFLoader(pdf_path)
docs = loader.load()

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

auth = os.getenv('SBER_21')
llm = GigaChat(credentials=auth,
              model='GigaChat:latest',
               verify_ssl_certs=False,
               profanity_check=False)

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
q1 = 'Компетенции системного аналитика уровня junior'
resp1 = retrieval_chain.invoke(
    {'input': q1}
)
print(resp1)