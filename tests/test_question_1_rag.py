import asyncio
import inspect

import pytest

# Импортируем модуль RAG-сервиса как обычную библиотеку
import src.main_version.rag_service as rag

QUESTION_TEXT = "Получить матрицу компетенций"
QUESTION_ID = 1
ROLE = "Специалист"
SPECIALIZATION = "Тестировщик"  # у пользователя, но в БД question имеет WEB-vector-store
VECTOR_STORE_SETTING = "web"  # явно указали в админке


@pytest.mark.asyncio
async def test_full_chain_question_1():
    """Проверяем выбор ретривера, генерацию запросов и результаты поиска для вопроса 1."""
    # 1. Выбор ретривера
    retriever = rag.get_best_retriever_for_role_spec(
        role=ROLE,
        specialization=SPECIALIZATION,
        vector_store_preference=VECTOR_STORE_SETTING,
    )
    # Проверяем, что выбрался именно web-retriever
    assert retriever is rag.embedding_retriever_web, "Ожидался retriever для WEB, получен другой"

    # 2. Генерация семантических поисковых запросов
    queries = await rag.generate_semantic_search_queries(
        question=QUESTION_TEXT,
        role=ROLE,
        specialization=SPECIALIZATION,
    )
    # Функция возвращает dict {"queries": [...], "debug": ...} либо список – учитываем оба случая
    if isinstance(queries, dict):
        queries_list = queries.get("queries") or queries.get("alternative_queries") or []
    else:
        queries_list = queries
    assert len(queries_list) >= 5, "Должно быть не менее 5 альтернативных запросов"

    # 3. Запуск улучшенного векторного поиска
    results = await rag.enhanced_vector_search(
        question=QUESTION_TEXT,
        role=ROLE,
        specialization=SPECIALIZATION,
        embedding_retriever=retriever,
        top_k=8,
    )
    # Проверяем, что найден хотя бы один документ и он из web-пакета
    assert results, "Поиск не вернул результатов"
    assert any("_web_" in doc.metadata.get("source", "") for doc in results), (
        "Результаты не содержат документов web-пакета"
    )

    # Выводим диагностическую информацию
    print("\n--- Диагностика теста вопроса 1 ---")
    print("Использованный retriever:", retriever)
    print("Сгенерированные поисковые запросы:")
    for q in queries_list:
        print("  •", q)
    print("\nТоп документов:")
    for i, doc in enumerate(results, 1):
        src = doc.metadata.get("source", "unknown")
        score = doc.metadata.get("score", "?")
        preview = doc.page_content[:120].replace("\n", " ")
        print(f"{i:2d}. score={score:.3f} | source={src} | {preview}…") 