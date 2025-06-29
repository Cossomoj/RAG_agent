#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('src/main_version')

from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
import string

def debug_vector_search():
    """
    Отладка векторного поиска для тестировщиков
    """
    print("🔍 Тест векторного поиска для Специалист + Тестировщик")
    print("="*60)
    
    # Эмулируем поиск как в RAG сервисе
    question = "Что я могу ожидать от своего PO/PM?"
    role = "Специалист"
    specialization = "Тестировщик"
    
    print(f"📋 Входные данные:")
    print(f"   Вопрос: {question}")
    print(f"   Роль: {role}")
    print(f"   Специализация: {specialization}")
    print()
    
    # Генерируем поисковые запросы как в RAG сервисе
    role_specific_terms = {
        'тестировщик': ['тестирование', 'качество', 'баги', 'QA', 'стратегия тестирования', 'критерии приемки'],
        'qa': ['тестирование', 'качество', 'баги', 'QA', 'стратегия тестирования', 'критерии приемки'],
        'аналитик': ['анализ требований', 'документация', 'бизнес-процессы', 'стейкхолдеры'],
    }
    
    spec_lower = specialization.lower() if specialization else ""
    specific_terms = []
    for key, terms in role_specific_terms.items():
        if key in spec_lower:
            specific_terms = terms
            break
    
    print(f"🎯 Специализированные термины для {specialization}: {specific_terms}")
    
    # Примеры поисковых запросов
    search_queries = [
        question,  # исходный вопрос
        f"взаимодействие {specialization} PO PM",
        f"ожидания от PO PM {specialization}",
        f"{specific_terms[0] if specific_terms else 'развитие'} специалист команда",
        f"обратная связь {specialization} проект",
        "взаимодействие тестировщик product owner",
        "ожидания QA от PM"
    ]
    
    print(f"📝 Поисковые запросы:")
    for i, query in enumerate(search_queries, 1):
        print(f"   {i}. {query}")
    print()
    
    # Симуляция поиска по документам
    print("📁 Симуляция поиска в документах:")
    
    # Ключевые слова для анализа
    qa_keywords = ['тестиров', 'качест', 'qa', 'баг', 'тест', 'критери', 'стратег']
    analyst_keywords = ['аналит', 'требован', 'документац', 'бизнес-процесс']
    
    # Анализ документов в папке Specialist
    docs_folder = "src/main_version/docs/Specialist"
    specialist_docs = []
    
    for root, dirs, files in os.walk(docs_folder):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Анализ контента
                    content_lower = content.lower()
                    qa_score = sum(1 for keyword in qa_keywords if keyword in content_lower)
                    analyst_score = sum(1 for keyword in analyst_keywords if keyword in content_lower)
                    
                    # Проверка релевантности к вопросу
                    question_keywords = ['po', 'pm', 'product owner', 'project manager', 'ожидать', 'взаимодейств']
                    relevance_score = sum(1 for keyword in question_keywords if keyword in content_lower)
                    
                    specialist_docs.append({
                        'file': file_path.replace('src/main_version/docs/Specialist/', ''),
                        'qa_score': qa_score,
                        'analyst_score': analyst_score,
                        'relevance_score': relevance_score,
                        'content_size': len(content)
                    })
                except Exception as e:
                    print(f"   ⚠️ Ошибка чтения {file}: {e}")
    
    # Сортировка по релевантности
    specialist_docs.sort(key=lambda x: (x['relevance_score'], x['qa_score']), reverse=True)
    
    print(f"📊 Топ-10 наиболее релевантных документов:")
    print(f"{'Файл':<50} {'Релев.':<6} {'QA':<4} {'Анал.':<6} {'Размер':<8}")
    print("-" * 80)
    
    for i, doc in enumerate(specialist_docs[:10], 1):
        file_display = doc['file'][:47] + "..." if len(doc['file']) > 50 else doc['file']
        print(f"{file_display:<50} {doc['relevance_score']:<6} {doc['qa_score']:<4} {doc['analyst_score']:<6} {doc['content_size']:<8}")
    
    print()
    print("🔍 Анализ проблемы:")
    
    # Подсчет общих метрик
    total_qa_docs = len([d for d in specialist_docs if 'QA' in d['file'] or 'qa' in d['file']])
    total_analyst_docs = len([d for d in specialist_docs if 'Analyst' in d['file'] or 'analyst' in d['file']])
    
    top_qa_docs = len([d for d in specialist_docs[:10] if 'QA' in d['file'] or 'qa' in d['file']])
    top_analyst_docs = len([d for d in specialist_docs[:10] if 'Analyst' in d['file'] or 'analyst' in d['file']])
    
    print(f"📈 Статистика документов:")
    print(f"   Всего QA документов: {total_qa_docs}")
    print(f"   Всего Analyst документов: {total_analyst_docs}")
    print(f"   QA документов в топ-10: {top_qa_docs}")
    print(f"   Analyst документов в топ-10: {top_analyst_docs}")
    
    if top_analyst_docs > top_qa_docs:
        print(f"❌ ПРОБЛЕМА: В топ-10 релевантных документов больше документов для аналитиков!")
        print(f"   Это объясняет, почему система выдает ответы про аналитиков для тестировщиков.")
    else:
        print(f"✅ Документы QA доминируют в топ-10, проблема не в векторном поиске.")

if __name__ == "__main__":
    debug_vector_search() 