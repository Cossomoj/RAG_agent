// Telegram Web App API
let tg = window.Telegram.WebApp;

// Конфигурация
const CONFIG = {
    API_BASE_URL: window.location.origin + '/api', // Будет работать с /var/www/html/api
    WEBSOCKET_URL: 'ws://213.171.25.85:8000/ws' // Ваш WebSocket сервер
};

// Состояние приложения
const AppState = {
    currentScreen: 'main-menu',
    user: null,
    profile: {
        role: '',
        specialization: ''
    },
    history: [],
    questions: []
};

// Инициализация приложения
document.addEventListener('DOMContentLoaded', async function() {
    initViewportFixes();
    initTelegramWebApp();
    await loadRolesAndSpecializations();
    await loadUserProfile();
    await loadHistory();
    await loadQuestions();
});

// Исправления для viewport на разных устройствах
function initViewportFixes() {
    // Фиксы для iOS Safari
    function setVhProperty() {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    }
    
    // Установка при загрузке
    setVhProperty();
    
    // Обновление при изменении размера окна (поворот экрана)
    window.addEventListener('resize', debounce(setVhProperty, 100));
    window.addEventListener('orientationchange', () => {
        setTimeout(setVhProperty, 100);
    });
    
    // Предотвращение масштабирования при двойном тапе
    let lastTouchEnd = 0;
    document.addEventListener('touchend', function (event) {
        const now = (new Date()).getTime();
        if (now - lastTouchEnd <= 300) {
            event.preventDefault();
        }
        lastTouchEnd = now;
    }, false);
    
    // Улучшенная обработка фокуса на мобильных устройствах
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            // Небольшая задержка для корректной работы на iOS
            setTimeout(() => {
                this.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
            }, 300);
        });
    });
}

// Утилита debounce для оптимизации производительности
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Инициализация Telegram Web App
function initTelegramWebApp() {
    try {
        // Расширяем приложение на весь экран
        tg.expand();
        
        // Настраиваем цвета в соответствии с темой Telegram
        tg.setHeaderColor('bg_color');
        
        // Получаем данные пользователя
        if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
            AppState.user = tg.initDataUnsafe.user;
            console.log('Пользователь Telegram:', AppState.user);
        }
        
        // Настраиваем главную кнопку
        tg.MainButton.text = 'Готово';
        tg.MainButton.hide();
        
        // Обработчик кнопки "Назад"
        tg.BackButton.onClick(() => {
            goBack();
        });
        
        console.log('Telegram Web App инициализирован');
    } catch (error) {
        console.error('Ошибка инициализации Telegram Web App:', error);
    }
}

// Навигация между экранами
async function showScreen(screenId) {
    // Скрываем все экраны
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    
    // Показываем нужный экран
    const targetScreen = document.getElementById(screenId);
    if (targetScreen) {
        targetScreen.classList.add('active');
        AppState.currentScreen = screenId;
        
        // Обновляем состояние кнопок Telegram
        updateTelegramButtons(screenId);
        
        // Загружаем данные для экрана
        await loadScreenData(screenId);
    }
}

// Обновление кнопок Telegram
function updateTelegramButtons(screenId) {
    if (screenId === 'main-menu') {
        tg.BackButton.hide();
    } else {
        tg.BackButton.show();
    }
    
    tg.MainButton.hide();
}

// Возврат назад
function goBack() {
    if (AppState.currentScreen === 'main-menu') {
        tg.close();
    } else {
        showScreen('main-menu');
    }
}

// Загрузка данных для экрана
async function loadScreenData(screenId) {
    switch (screenId) {
        case 'questions-library':
            renderQuestions();
            break;
        case 'history':
            await loadHistory();
            renderHistory();
            break;
        case 'profile':
            renderProfile();
            break;
        case 'feedback':
            initFeedbackScreen();
            break;
    }
}

// === ПРОФИЛЬ ===

// Загрузка профиля пользователя
async function loadUserProfile() {
    try {
        const userId = AppState.user?.id || 'guest';
        const response = await fetch(`${CONFIG.API_BASE_URL}/profile/${userId}`);
        
        if (response.ok) {
            const profile = await response.json();
            AppState.profile = profile;
        }
    } catch (error) {
        console.error('Ошибка загрузки профиля:', error);
    }
}

// Глобальные переменные для ролей и специализаций (загружаются из API)
let roles = [];
let specializations = [];

// Загрузка ролей и специализаций
async function loadRolesAndSpecializations() {
    try {
        const [rolesResponse, specsResponse] = await Promise.all([
            fetch(`${CONFIG.API_BASE_URL}/roles`),
            fetch(`${CONFIG.API_BASE_URL}/specializations`)
        ]);
        
        if (rolesResponse.ok && specsResponse.ok) {
            roles = await rolesResponse.json();
            specializations = await specsResponse.json();
        } else {
            throw new Error('Ошибка загрузки данных');
        }
    } catch (error) {
        console.error('Ошибка загрузки ролей и специализаций:', error);
        // Fallback значения из телеграм бота
        roles = [
            { value: 'PO/PM', label: 'PO/PM' },
            { value: 'Лид компетенции', label: 'Лид компетенции' },
            { value: 'Специалист', label: 'Специалист' },
            { value: 'Стажер', label: 'Стажер' }
        ];
        specializations = [
            { value: 'Аналитик', label: 'Аналитик' },
            { value: 'Тестировщик', label: 'Тестировщик' },
            { value: 'WEB', label: 'WEB' },
            { value: 'Java', label: 'Java' },
            { value: 'Python', label: 'Python' }
        ];
    }
}

// Обновление специализаций при выборе роли
function updateSpecializations() {
    const roleSelect = document.getElementById('role-select');
    const specializationSelect = document.getElementById('specialization-select');
    const role = roleSelect.value;
    
    // Очищаем список специализаций
    specializationSelect.innerHTML = '<option value="">Выберите специализацию</option>';
    
    // Для PO/PM специализация устанавливается автоматически
    if (role === 'PO/PM') {
        const option = document.createElement('option');
        option.value = 'PO/PM';
        option.textContent = 'PO/PM';
        option.selected = true;
        specializationSelect.appendChild(option);
        specializationSelect.disabled = true;
    } else {
        // Для других ролей показываем все доступные специализации
        specializationSelect.disabled = false;
        specializations.forEach(spec => {
            const option = document.createElement('option');
            option.value = spec.value;
            option.textContent = spec.label;
            specializationSelect.appendChild(option);
        });
    }
    
    // Обновляем информацию профиля при изменении
    setTimeout(() => {
        updateProfileInfo();
    }, 100);
}

// Обновление информации профиля
function updateProfileInfo() {
    const profileName = document.getElementById('profile-name');
    const profileStatus = document.getElementById('profile-status');
    
    if (AppState.profile.role && AppState.profile.specialization) {
        profileName.textContent = `${AppState.profile.role} • ${AppState.profile.specialization}`;
        profileStatus.textContent = 'Профиль настроен';
    } else {
        profileName.textContent = 'Настройка профиля';
        profileStatus.textContent = 'Заполните информацию о себе';
    }
}

// Отображение профиля
function renderProfile() {
    const roleSelect = document.getElementById('role-select');
    const specializationSelect = document.getElementById('specialization-select');
    
    // Заполняем список ролей
    roleSelect.innerHTML = '<option value="">Выберите вашу роль</option>';
    roles.forEach(role => {
        const option = document.createElement('option');
        option.value = role.value;
        option.textContent = role.label;
        roleSelect.appendChild(option);
    });
    
    // Устанавливаем значения из профиля
    if (AppState.profile.role) {
        roleSelect.value = AppState.profile.role;
        updateSpecializations();
        
        if (AppState.profile.specialization) {
            specializationSelect.value = AppState.profile.specialization;
        }
    }
    
    // Добавляем обработчики изменений
    roleSelect.addEventListener('change', function() {
        AppState.profile.role = this.value;
        updateProfileInfo();
    });
    
    specializationSelect.addEventListener('change', function() {
        AppState.profile.specialization = this.value;
        updateProfileInfo();
    });
    
    // Обновляем информацию о профиле
    updateProfileInfo();
}

// Сохранение профиля
async function saveProfile() {
    const roleSelect = document.getElementById('role-select');
    const specializationSelect = document.getElementById('specialization-select');
    
    AppState.profile.role = roleSelect.value;
    AppState.profile.specialization = specializationSelect.value;
    
    if (!AppState.profile.role || !AppState.profile.specialization) {
        showAlert('Пожалуйста, заполните все поля профиля');
        return;
    }
    
    try {
        const userId = AppState.user?.id || 'guest';
        const response = await fetch(`${CONFIG.API_BASE_URL}/profile/${userId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(AppState.profile)
        });
        
        if (response.ok) {
            await loadQuestions(); // Перезагружаем вопросы для новой роли
            showAlert('Профиль сохранен!');
            showScreen('main-menu');
        } else {
            throw new Error('Ошибка сохранения профиля');
        }
    } catch (error) {
        console.error('Ошибка сохранения профиля:', error);
        showAlert('Ошибка сохранения профиля');
    }
}

// === ВОПРОСЫ ===

// Отображение заданного вопроса
function displayAskedQuestion(question) {
    const askedQuestionContainer = document.getElementById('asked-question-container');
    const askedQuestionText = document.getElementById('asked-question-text');
    
    askedQuestionText.textContent = question;
    askedQuestionContainer.classList.remove('hidden');
}

// Отправка вопроса
async function sendQuestion() {
    const questionInput = document.getElementById('question-input');
    const sendBtn = document.getElementById('send-question');
    const btnText = sendBtn.querySelector('.btn-text');
    const spinner = sendBtn.querySelector('.spinner');
    
    const question = questionInput.value.trim();
    if (!question) {
        showAlert('Пожалуйста, введите вопрос');
        return;
    }
    
    // Показываем заданный вопрос
    displayAskedQuestion(question);
    
    // Сохраняем вопрос пользователя для генерации связанных вопросов
    SuggestedQuestionsState.userQuestion = question;
    
    // Показываем полноэкранный лоадер
    showLoader();
    
    // Показываем лоадер на кнопке
    sendBtn.disabled = true;
    btnText.textContent = 'Отправляем...';
    spinner.classList.remove('hidden');
    
    try {
        const userId = AppState.user?.id || 'guest';
        
        // Создаем системный промпт для улучшения форматирования
        const systemPrompt = `Отвечай структурированно и читабельно:
- Используй нумерованные списки (1., 2., 3.) для пошаговых инструкций
- Используй маркированные списки (-, *) для перечислений
- Выделяй важные термины **жирным шрифтом**
- Используй заголовки ### для разделов
- Соблюдай правильную пунктуацию и грамматику
- Каждый пункт списка начинай с новой строки
- Делай абзацы для лучшей читабельности

Вопрос пользователя: ${question}`;
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question, // только текст вопроса пользователя!
                user_id: userId,
                role: AppState.profile.role,
                specialization: AppState.profile.specialization
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            displayAnswer(data.answer, data.suggested_questions);
            
            // Добавляем в локальную историю
            AppState.history.unshift({
                id: Date.now(),
                question: question,
                answer: data.answer,
                timestamp: new Date(),
                role: AppState.profile.role,
                specialization: AppState.profile.specialization
            });
            
            // Перезагружаем историю из БД с задержкой, чтобы дать время серверу сохранить ответ
            setTimeout(async () => {
                await loadHistory();
                console.log('✅ История обновлена из БД');
            }, 500);
            
            // Очищаем поле ввода
            questionInput.value = '';
        } else {
            throw new Error('Ошибка получения ответа');
        }
    } catch (error) {
        console.error('Ошибка отправки вопроса:', error);
        showAlert('Ошибка отправки вопроса. Попробуйте снова.');
    } finally {
        // Скрываем полноэкранный лоадер
        hideLoader();
        
        // Скрываем лоадер на кнопке
        sendBtn.disabled = false;
        btnText.textContent = 'Отправить';
        spinner.classList.add('hidden');
    }
}

// Отображение ответа
// Состояние для связанных вопросов
const SuggestedQuestionsState = {
    currentQuestions: [],
    userQuestion: '',
    botAnswer: ''
};

// Функция для форматирования ответа с улучшенной пунктуацией и читабельностью
function formatAnswerText(text) {
    if (!text) return '';
    
    // Убираем лишние пробелы и нормализуем переносы строк
    let formatted = text.trim().replace(/\s+/g, ' ');
    
    // Удаляем символы # в начале строки и подряд идущие #
    formatted = formatted.replace(/#+/g, '');
    formatted = formatted.replace(/^\s*#+/gm, '');
    
    // Добавляем переносы перед нумерованными списками (1., 2., 3. и т.д.)
    formatted = formatted.replace(/(\S)\s*(\d+\.\s+)/g, '$1\n\n$2');
    
    // Добавляем переносы перед маркированными списками (-, *, •)
    formatted = formatted.replace(/(\S)\s*([-*•]\s+)/g, '$1\n\n$2');
    
    // Добавляем переносы только после точек, если следующее предложение очень длинное (более 80 символов)
    formatted = formatted.replace(/\.\s+([А-ЯA-Z][^.!?]{80,})/g, '.\n\n$1');
    
    // Добавляем переносы после двоеточий для лучшей структуры
    formatted = formatted.replace(/:\s+([А-ЯA-Z][^:]{50,})/g, ':\n\n$1');
    
    // Убираем множественные переносы строк (более 2 подряд)
    formatted = formatted.replace(/\n{3,}/g, '\n\n');
    
    return formatted.trim();
}

// Преобразование Markdown в HTML
function convertMarkdownToHtml(text) {
    if (!text) return '';
    
    let html = text;
    
    // Жирный текст: **текст** или __текст__
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__(.*?)__/g, '<strong>$1</strong>');
    
    // Курсивный текст: *текст* или _текст_
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    html = html.replace(/_(.*?)_/g, '<em>$1</em>');
    
    // Заголовки: ### Заголовок
    html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');
    
    // Код: `код`
    html = html.replace(/`(.*?)`/g, '<code>$1</code>');
    
    // Обработка нумерованных списков
    const numberedListItems = [];
    html = html.replace(/^\d+\.\s+(.*)$/gm, (match, content) => {
        numberedListItems.push(`<li>${content.trim()}</li>`);
        return `NUMBERED_LIST_ITEM_${numberedListItems.length - 1}`;
    });
    
    // Обработка маркированных списков  
    const bulletListItems = [];
    html = html.replace(/^[-*•]\s+(.*)$/gm, (match, content) => {
        bulletListItems.push(`<li>${content.trim()}</li>`);
        return `BULLET_LIST_ITEM_${bulletListItems.length - 1}`;
    });
    
    // Переносы строк в параграфы
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';
    
    // Восстанавливаем нумерованные списки
    if (numberedListItems.length > 0) {
        let numberedListHtml = '<ol>' + numberedListItems.join('') + '</ol>';
        html = html.replace(/NUMBERED_LIST_ITEM_\d+/g, '');
        html = html.replace(/<p><\/p>/g, '');
        html += numberedListHtml;
    }
    
    // Восстанавливаем маркированные списки
    if (bulletListItems.length > 0) {
        let bulletListHtml = '<ul>' + bulletListItems.join('') + '</ul>';
        html = html.replace(/BULLET_LIST_ITEM_\d+/g, '');
        html = html.replace(/<p><\/p>/g, '');
        html += bulletListHtml;
    }
    
    // Убираем пустые параграфы
    html = html.replace(/<p><\/p>/g, '');
    html = html.replace(/<p>\s*<\/p>/g, '');
    
    return html;
}

// Отображение предыдущих вопросов из истории
async function displayPreviousQuestions() {
    console.log('📜 displayPreviousQuestions вызвана');
    
    const previousContainer = document.getElementById('previous-questions');
    const previousList = document.getElementById('previous-list');
    
    try {
        // Загружаем актуальную историю из БД
        const userId = AppState.user?.id || 'guest';
        console.log('🔄 Загружаем актуальную историю из БД для userId:', userId);
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/history/${userId}`);
        if (!response.ok) {
            console.error('❌ Ошибка загрузки истории:', response.status);
            previousContainer.classList.add('hidden');
            return;
        }
        
        const historyFromDB = await response.json();
        console.log('📊 История из БД:', historyFromDB);
        console.log('📊 Длина истории из БД:', historyFromDB ? historyFromDB.length : 'undefined');
        
        if (!historyFromDB || historyFromDB.length === 0) {
            console.log('⚠️ История из БД пуста');
            previousContainer.classList.add('hidden');
            return;
        }
        
        // Получаем последние 3 вопроса из истории (исключая самый последний, который является текущим)
        const previousQuestions = historyFromDB.slice(1, 4); // Пропускаем первый (текущий) вопрос
        
        console.log('📍 Предыдущие вопросы из БД:', previousQuestions);
        console.log('📍 Количество предыдущих вопросов:', previousQuestions.length);
        
        if (!previousQuestions || previousQuestions.length === 0) {
            console.log('⚠️ Нет предыдущих вопросов для отображения');
            previousContainer.classList.add('hidden');
            return;
        }
        
        console.log('🔄 Создаем кнопки предыдущих вопросов...');
        previousList.innerHTML = '';
        
        previousQuestions.forEach((historyItem, index) => {
            console.log(`➕ Добавляем предыдущий вопрос ${index + 1}:`, historyItem.question.substring(0, 50));
            const button = document.createElement('button');
            button.className = 'previous-question-btn';
            button.textContent = historyItem.question;
            button.onclick = () => {
                console.log('🔄 Пользователь выбрал предыдущий вопрос:', historyItem.question);
                showHistoryDetail(historyItem);
            };
            previousList.appendChild(button);
        });
        
        previousContainer.classList.remove('hidden');
        console.log('✅ Предыдущие вопросы отображены');
        
    } catch (error) {
        console.error('❌ Ошибка загрузки предыдущих вопросов:', error);
        previousContainer.classList.add('hidden');
    }
}

function displayAnswer(answer, suggestedQuestions = []) {
    console.log('📄 displayAnswer вызвана с ответом длиной:', answer.length, 'символов');
    
    const answerContainer = document.getElementById('answer-container');
    const answerText = document.getElementById('answer-text');
    const suggestedContainer = document.getElementById('suggested-questions');
    
    // Форматируем ответ для лучшей читабельности
    const formattedAnswer = formatAnswerText(answer);
    
    // Преобразуем Markdown в HTML
    const htmlAnswer = convertMarkdownToHtml(formattedAnswer);
    
    answerText.innerHTML = htmlAnswer;
    answerContainer.classList.remove('hidden');
    
    // Сохраняем данные для генерации связанных вопросов
    SuggestedQuestionsState.botAnswer = answer;
    console.log('💾 Ответ сохранен в SuggestedQuestionsState:', {
        userQuestion: SuggestedQuestionsState.userQuestion,
        botAnswer: SuggestedQuestionsState.botAnswer.substring(0, 50) + '...'
    });
    
    // Прокрутка к самому верху страницы сразу после вывода ответа
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Если есть готовые связанные вопросы, показываем их
    if (suggestedQuestions && suggestedQuestions.length > 0) {
        console.log('🔗 Показываем готовые связанные вопросы:', suggestedQuestions);
        displaySuggestedQuestions(suggestedQuestions);
    } else {
        console.log('🤖 Генерируем связанные вопросы...');
        // Генерируем связанные вопросы асинхронно
        generateSuggestedQuestions();
    }
    
    // Показываем предыдущие вопросы из истории в самом конце
    setTimeout(async () => {
        await displayPreviousQuestions();
    }, 100);
}

// Генерация связанных вопросов как в телеграм боте
async function generateSuggestedQuestions() {
    console.log('🔄 Начинаем генерацию связанных вопросов...');
    
    const payload = {
        user_question: SuggestedQuestionsState.userQuestion,
        bot_answer: SuggestedQuestionsState.botAnswer.substring(0, 2000), // Обрезаем как в боте
        role: AppState.profile.role || 'Пользователь',
        specialization: AppState.profile.specialization || 'Не указана'
    };
    
    console.log('📝 Payload для генерации вопросов:', payload);
    
    // Проверяем, что у нас есть необходимые данные
    if (!SuggestedQuestionsState.userQuestion || !SuggestedQuestionsState.botAnswer) {
        console.warn('⚠️ Недостаточно данных для генерации вопросов');
        return;
    }
    
    try {
        console.log('🔌 Попытка подключения к WebSocket ws://127.0.0.1:8000/ws_suggest');
        
        // Таймаут для WebSocket соединения
        const wsPromise = new Promise((resolve, reject) => {
            const ws = new WebSocket('ws://127.0.0.1:8000/ws_suggest');
            let connected = false;
            
            // Таймаут соединения
            const timeout = setTimeout(() => {
                if (!connected) {
                    console.warn('⏱️ WebSocket соединение превысило таймаут');
                    ws.close();
                    reject(new Error('WebSocket connection timeout'));
                }
            }, 5000);
            
            ws.onopen = () => {
                connected = true;
                clearTimeout(timeout);
                console.log('✅ WebSocket соединение установлено');
                ws.send(JSON.stringify(payload));
                console.log('📤 Данные отправлены на сервер');
            };
            
            ws.onmessage = (event) => {
                console.log('📥 Получен ответ от сервера:', event.data);
                try {
                    const questions = JSON.parse(event.data);
                    
                    if (questions && questions.error) {
                        console.error('❌ Ошибка от сервера:', questions.error);
                        reject(new Error(questions.error));
                        return;
                    }
                    
                    if (Array.isArray(questions) && questions.length > 0) {
                        console.log('🎯 Успешно получены вопросы:', questions);
                        // Берем только первые 3 вопроса как в боте
                        SuggestedQuestionsState.currentQuestions = questions.slice(0, 3);
                        displaySuggestedQuestions(SuggestedQuestionsState.currentQuestions);
                        resolve(questions);
                    } else {
                        console.warn('⚠️ Получен некорректный ответ или пустой список вопросов:', questions);
                        resolve([]);
                    }
                } catch (error) {
                    console.error('❌ Ошибка парсинга ответа:', error);
                    reject(error);
                } finally {
                    ws.close();
                }
            };
            
            ws.onerror = (error) => {
                connected = true; // Останавливаем таймаут
                clearTimeout(timeout);
                console.error('❌ WebSocket ошибка:', error);
                reject(error);
            };
            
            ws.onclose = (event) => {
                console.log('🔌 WebSocket соединение закрыто:', event.code, event.reason);
            };
        });
        
        await wsPromise;
        
    } catch (error) {
        console.error('❌ Ошибка WebSocket соединения:', error);
        console.log('🔄 Пробуем альтернативный способ через HTTP API...');
        
        // Fallback: пробуем через HTTP API
        try {
            const response = await fetch(`${CONFIG.API_BASE_URL}/suggest_questions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            if (response.ok) {
                const questions = await response.json();
                console.log('✅ Получены вопросы через HTTP API:', questions);
                
                if (Array.isArray(questions) && questions.length > 0) {
                    SuggestedQuestionsState.currentQuestions = questions.slice(0, 3);
                    displaySuggestedQuestions(SuggestedQuestionsState.currentQuestions);
                }
            } else {
                console.error('❌ HTTP API также недоступен:', response.status, response.statusText);
            }
        } catch (httpError) {
            console.error('❌ Ошибка HTTP fallback:', httpError);
            console.log('💡 Для получения связанных вопросов убедитесь, что RAG сервис запущен на порту 8000');
        }
    }
}

// Отображение связанных вопросов
function displaySuggestedQuestions(questions) {
    console.log('🎯 displaySuggestedQuestions вызвана с вопросами:', questions);
    
    const suggestedContainer = document.getElementById('suggested-questions');
    const suggestedList = document.getElementById('suggested-list');
    const answerContainer = document.getElementById('answer-container');
    
    console.log('📍 Элементы DOM найдены:', {
        suggestedContainer: !!suggestedContainer,
        suggestedList: !!suggestedList,
        answerContainer: !!answerContainer
    });
    
    if (!questions || questions.length === 0) {
        console.log('⚠️ Нет вопросов для отображения');
        suggestedContainer.classList.add('hidden');
        return;
    }
    
    console.log('🔄 Очищаем и создаем новые кнопки вопросов...');
    suggestedList.innerHTML = '';
    
    questions.forEach((question, index) => {
        console.log(`➕ Добавляем вопрос ${index + 1}:`, question);
        const button = document.createElement('button');
        button.className = 'suggested-question-btn';
        button.textContent = question;
        button.onclick = () => {
            console.log('🔄 Пользователь выбрал связанный вопрос:', question);
            document.getElementById('question-input').value = question;
            sendQuestion();
        };
        suggestedList.appendChild(button);
    });
    
    // Перемещаем блок в конец answer-container
    if (answerContainer && suggestedContainer) {
        answerContainer.appendChild(suggestedContainer);
    }
    
    suggestedContainer.classList.remove('hidden');
    console.log('✅ Связанные вопросы отображены');
}

// === БИБЛИОТЕКА ВОПРОСОВ ===

// Состояние библиотеки вопросов
const LibraryState = {};

// Загрузка готовых вопросов
async function loadQuestions() {
    const questionsList = document.getElementById('questions-list');
    
    // Показываем скелетоны загрузки
    if (questionsList) {
        showQuestionsLoadingSkeleton(questionsList);
    }
    
    try {
        const params = new URLSearchParams();
        if (AppState.profile.role) {
            params.append('role', AppState.profile.role);
        }
        if (AppState.profile.specialization) {
            params.append('specialization', AppState.profile.specialization);
        }
        
        const url = `${CONFIG.API_BASE_URL}/questions${params.toString() ? '?' + params.toString() : ''}`;
        const response = await fetch(url);
        
        if (response.ok) {
            AppState.questions = await response.json();
        }
    } catch (error) {
        console.error('Ошибка загрузки вопросов:', error);
    } finally {
        // Всегда рендерим результат (даже если произошла ошибка)
        renderQuestions();
    }
}

// Отображение вопросов
function renderQuestions() {
    const questionsList = document.getElementById('questions-list');
    const questions = AppState.questions || [];
    
    questionsList.innerHTML = '';
    
    if (questions.length === 0) {
        const emptyState = document.createElement('div');
        emptyState.className = 'empty-state';
        emptyState.innerHTML = `
            <div style="text-align: center; padding: 40px 20px; color: var(--tg-theme-hint-color);">
                <div style="font-size: 48px; margin-bottom: 16px; animation: bounce 2s ease-in-out infinite;">📝</div>
                <h3 style="margin: 0 0 8px 0; font-size: 18px; font-weight: 600;">Вопросы не найдены</h3>
                <p style="margin: 0; font-size: 14px; line-height: 1.5;">Заполните профиль для получения персонализированных вопросов</p>
            </div>
        `;
        questionsList.appendChild(emptyState);
        return;
    }
    
    questions.forEach((question, index) => {
        const div = document.createElement('div');
        div.className = 'question-item';
        div.setAttribute('data-category', question.category);
        
        const preview = question.preview || question.text.substring(0, 120) + '...';
        
        div.innerHTML = `
            <div class="question-header">
                <div class="question-meta">
                    <div class="question-icon">${getCategoryIcon(question.category)}</div>
                    <div class="question-title">${question.title}</div>
                </div>
                <div class="question-category">${getCategoryName(question.category)}</div>
            </div>
            <div class="question-preview">${preview}</div>
        `;
        
        div.onclick = async () => await useQuestionDirectly(index);
        questionsList.appendChild(div);
    });
}

// Использование вопроса напрямую из библиотеки с кешированием
async function useQuestionDirectly(index) {
    const questions = AppState.questions || [];
    const question = questions[index];
    
    if (!question) {
        showAlert('Вопрос не найден');
        return;
    }
    
    // Показываем заданный вопрос
    displayAskedQuestion(question.text);
    
    // Сохраняем вопрос пользователя для генерации связанных вопросов
    SuggestedQuestionsState.userQuestion = question.text;
    
    // Показываем полноэкранный лоадер
    showLoader();
    
    try {
        const userId = AppState.user?.id || 'guest';
        
        // Используем специальный endpoint для библиотечных вопросов с кешированием
        const response = await fetch(`${CONFIG.API_BASE_URL}/ask_library`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question.text,
                question_id: question.id, // Передаем ID вопроса для кеширования
                user_id: userId,
                role: AppState.profile.role,
                specialization: AppState.profile.specialization
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            displayAnswer(data.answer, data.suggested_questions);
            
            // Добавляем в локальную историю
            AppState.history.unshift({
                id: Date.now(),
                question: question.text,
                answer: data.answer,
                timestamp: new Date(),
                role: AppState.profile.role,
                specialization: AppState.profile.specialization,
                cached: data.cached || false
            });
            
            // Перезагружаем историю из БД с задержкой
            setTimeout(async () => {
                await loadHistory();
                console.log('✅ История обновлена из БД');
            }, 500);
            
            // Переходим к экрану с ответом
            showScreen('ask-question');
        } else {
            throw new Error('Ошибка получения ответа');
        }
    } catch (error) {
        console.error('Ошибка отправки библиотечного вопроса:', error);
        showAlert('Ошибка получения ответа. Попробуйте снова.');
    } finally {
        // Скрываем полноэкранный лоадер
        hideLoader();
    }
}

// Получение названия категории
function getCategoryName(category) {
    const names = {
        'Взаимодействие': 'Взаимодействие',
        'Обязанности': 'Обязанности',
        'Развитие': 'Развитие',
        'Дополнительно': 'Дополнительно',
        'development': 'Разработка',
        'analysis': 'Аналитика',
        'management': 'Управление',
        'testing': 'Тестирование'
    };
    return names[category] || category;
}

// Получение иконки для категории
function getCategoryIcon(category) {
    const icons = {
        'Взаимодействие': '🤝',
        'Обязанности': '📋',
        'Развитие': '📈',
        'Дополнительно': '💡',
        'development': '💻',
        'analysis': '📊',
        'management': '👥',
        'testing': '🧪'
    };
    return icons[category] || '❓';
}

// Получение иконки для роли
function getRoleIcon(role) {
    const icons = {
        'Разработчик': '👨‍💻',
        'Аналитик': '📊',
        'Тестировщик': '🧪',
        'Менеджер': '👔',
        'Дизайнер': '🎨',
        'DevOps': '⚙️',
        'Архитектор': '🏗️',
        'Продукт-менеджер': '📱',
        'Scrum-мастер': '🎯',
        'Технический писатель': '📝'
    };
    return icons[role] || '👤';
}

// === ИСТОРИЯ ===

// Загрузка истории
async function loadHistory() {
    const userId = AppState.user?.id || 'guest';
    const historyList = document.getElementById('history-list');
    
    console.log('Загружаем историю для userId:', userId);
    
    // Показываем скелетоны загрузки
    if (historyList) {
        showHistoryLoadingSkeleton(historyList);
    }
    
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/history/${userId}`);
        if (response.ok) {
            AppState.history = await response.json();
            console.log('Загружена история:', AppState.history);
        } else {
            console.error('Ошибка ответа сервера:', response.status, await response.text());
        }
    } catch (error) {
        console.error('Ошибка загрузки истории:', error);
    } finally {
        // Всегда рендерим результат
        renderHistory();
    }
}

// Отображение истории
function renderHistory() {
    const historyList = document.getElementById('history-list');
    historyList.innerHTML = '';
    
    console.log('Рендерим историю, количество элементов:', AppState.history.length);
    
    AppState.history.forEach((item, index) => {
        const div = document.createElement('div');
        div.className = 'history-item';
        
        const date = new Date(item.timestamp);
        const dateStr = date.toLocaleDateString('ru-RU', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const roleIcon = getRoleIcon(item.role);
        const questionPreview = item.question.substring(0, 50) + (item.question.length > 50 ? '...' : '');
        const answerPreview = item.answer.substring(0, 100) + (item.answer.length > 100 ? '...' : '');
        
        div.innerHTML = `
            <div class="history-header">
                <div class="history-meta">
                    <div class="history-icon">${roleIcon}</div>
                    <div class="history-title">${questionPreview}</div>
                </div>
            </div>
            <div class="history-preview">${answerPreview}</div>
        `;
        
        div.onclick = () => {
            console.log('Клик по элементу истории:', index, item);
            showHistoryDetail(item);
        };
        
        historyList.appendChild(div);
    });
    
    if (AppState.history.length === 0) {
        historyList.innerHTML = `
            <div style="text-align: center; padding: 40px 20px; color: var(--tg-theme-hint-color);">
                <div style="font-size: 48px; margin-bottom: 16px; animation: bounce 2s ease-in-out infinite;">📜</div>
                <h3 style="margin: 0 0 8px 0; font-size: 18px; font-weight: 600;">История пуста</h3>
                <p style="margin: 0; font-size: 14px; line-height: 1.5;">Задайте первый вопрос, чтобы начать диалог</p>
            </div>
        `;
    }
}

// Показ детальной информации из истории
function showHistoryDetail(item) {
    const modal = document.getElementById('history-modal');
    const historyDetail = document.getElementById('history-detail');
    
    console.log('Открываем модальное окно истории для:', item);
    console.log('Modal element:', modal);
    console.log('History detail element:', historyDetail);
    
    if (!modal || !historyDetail) {
        console.error('Не найдены элементы модального окна');
        return;
    }
    
    // Форматируем ответ для лучшей читабельности
    const formattedAnswer = formatAnswerText(item.answer);
    
    // Заполняем содержимое модального окна
    historyDetail.innerHTML = `
        <div class="question-block">
            <h4>Вопрос</h4>
            <p>${item.question}</p>
        </div>
        <div class="answer-block">
            <h4>Ответ</h4>
            <p style="white-space: pre-wrap;">${formattedAnswer}</p>
        </div>
    `;
    
    // Показываем модальное окно (используем новый стиль)
    modal.style.display = 'flex';
    modal.classList.remove('hidden');
    modal.classList.add('active');
    
    console.log('Модальное окно должно быть видимым:', modal.classList.contains('active'));
    
    // Закрытие по клику вне модального окна
    modal.onclick = (e) => {
        if (e.target === modal) {
            closeHistoryModal();
        }
    };
}

// Закрытие модального окна истории
function closeHistoryModal() {
    const modal = document.getElementById('history-modal');
    modal.classList.remove('active');
    modal.classList.add('hidden');
    
    // Добавляем небольшую задержку перед скрытием для анимации
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

// Обработка клавиши Escape для закрытия модальных окон
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const historyModal = document.getElementById('history-modal');
        
        if (historyModal.classList.contains('active') || !historyModal.classList.contains('hidden')) {
            closeHistoryModal();
        }
    }
});

// Очистка истории
async function clearHistory() {
    if (!confirm('Вы уверены, что хотите очистить историю?')) {
        return;
    }
    
    try {
        const userId = AppState.user?.id || 'guest';
        const response = await fetch(`${CONFIG.API_BASE_URL}/history/${userId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            AppState.history = [];
            renderHistory();
            showAlert('История очищена');
        }
    } catch (error) {
        console.error('Ошибка очистки истории:', error);
        showAlert('Ошибка очистки истории');
    }
}

// === УТИЛИТЫ ===

// Показ уведомления
function showAlert(message) {
    // Используем нативные уведомления Telegram если доступны
    if (tg.showAlert) {
        tg.showAlert(message);
    } else {
        alert(message);
    }
}

// Показ лоадера
function showLoader() {
    document.getElementById('loader').classList.remove('hidden');
}

// Скрытие лоадера
function hideLoader() {
    document.getElementById('loader').classList.add('hidden');
}

// Обработка ошибок сети
window.addEventListener('online', () => {
    showAlert('Соединение восстановлено');
});

window.addEventListener('offline', () => {
    showAlert('Потеряно соединение с интернетом');
});

// Обработка закрытия приложения
window.addEventListener('beforeunload', () => {
    // Сохраняем состояние в локальное хранилище
    localStorage.setItem('ragapp_state', JSON.stringify({
        profile: AppState.profile,
        history: AppState.history.slice(0, 10) // Сохраняем только последние 10 записей
    }));
});

// Восстановление состояния при загрузке
try {
    const savedState = localStorage.getItem('ragapp_state');
    if (savedState) {
        const state = JSON.parse(savedState);
        if (state.profile) {
            AppState.profile = { ...AppState.profile, ...state.profile };
        }
        if (state.history) {
            AppState.history = state.history;
        }
    }
} catch (error) {
    console.error('Ошибка восстановления состояния:', error);
}

// === ОБРАТНАЯ СВЯЗЬ ===

// Инициализация счетчика символов
function initCharCounter() {
    const textarea = document.getElementById('feedback-input');
    const charCount = document.getElementById('char-count');
    
    if (textarea && charCount) {
        // Обновляем счетчик при вводе
        textarea.addEventListener('input', () => {
            const currentLength = textarea.value.length;
            charCount.textContent = currentLength;
            
            // Меняем цвет при приближении к лимиту
            if (currentLength > 800) {
                charCount.style.color = '#ff6b6b';
            } else if (currentLength > 600) {
                charCount.style.color = '#f39c12';
            } else {
                charCount.style.color = '';
            }
        });
        
        // Инициализируем счетчик
        charCount.textContent = textarea.value.length;
    }
}

// Безопасный alert для Telegram WebApp
function safeAlert(msg) {
    // Удаляем переносы строк, markdown, emoji и ограничиваем длину
    let safe = String(msg)
        .replace(/[\n\r]+/g, ' ')
        .replace(/[\*\_\~\`\>\#\[\]\(\)\!]/g, '') // markdown
        .replace(/[^\x20-\x7Eа-яА-ЯёЁ0-9.,:;!?@\-]/g, '') // только базовые символы
        .slice(0, 200);
    showAlert(safe);
}

// Улучшенная отправка обратной связи
async function sendFeedback() {
    const feedbackInput = document.getElementById('feedback-input');
    const sendBtn = document.getElementById('feedback-submit-btn');
    const btnText = sendBtn.querySelector('.btn-text');
    const spinner = sendBtn.querySelector('.spinner');
    const feedbackForm = document.querySelector('.feedback-form');
    const feedbackSuccess = document.getElementById('feedback-success');
    
    const feedback = feedbackInput.value.trim();
    if (!feedback) {
        safeAlert('Пожалуйста, введите ваш отзыв');
        feedbackInput.focus();
        return;
    }
    
    if (feedback.length < 10) {
        safeAlert('Пожалуйста, напишите более подробный отзыв (минимум 10 символов)');
        feedbackInput.focus();
        return;
    }
    
    // Показываем лоадер на кнопке
    sendBtn.disabled = true;
    btnText.textContent = 'Отправляем...';
    spinner.classList.remove('hidden');
    
    // Добавляем эффект загрузки на кнопку
    sendBtn.style.transform = 'scale(0.98)';
    
    try {
        const userId = AppState.user?.id || 'guest';
        const userName = AppState.user?.first_name || 'Пользователь';
        const userUsername = AppState.user?.username || 'не указан';
        
        // Очищаем данные от потенциально проблемных символов
        const cleanFeedback = feedback.replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, '').trim();
        const cleanUserName = String(userName).replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, '').trim() || 'Пользователь';
        const cleanUsername = String(userUsername).replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]/g, '').trim() || 'не указан';
        
        console.log('Исходные данные пользователя:', {
            userId: userId,
            userName: userName,
            userUsername: userUsername,
            feedback: feedback
        });
        
        console.log('Очищенные данные:', {
            userId: userId,
            userName: cleanUserName,
            userUsername: cleanUsername,
            feedback: cleanFeedback
        });
        
        const requestData = {
            feedback: cleanFeedback,
            user_id: userId,
            user_name: cleanUserName,
            username: cleanUsername,
            role: AppState.profile.role || 'Не указана',
            specialization: AppState.profile.specialization || 'Не указана',
            category: 'general'
        };
        
        console.log('Отправляем данные обратной связи:', requestData);
        console.log('URL:', `${CONFIG.API_BASE_URL}/feedback`);
        
        // Сначала проверим соединение с сервером
        try {
            const testResponse = await fetch(`${CONFIG.API_BASE_URL}/test`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({test: 'connection'})
            });
            console.log('Тест соединения:', testResponse.status, testResponse.statusText);
            if (!testResponse.ok) {
                throw new Error(`Сервер недоступен: ${testResponse.status}`);
            }
        } catch (testError) {
            console.error('Ошибка соединения с сервером:', testError);
            throw new Error('Не удается подключиться к серверу. Проверьте, что сервер запущен.');
        }
        
        const response = await fetch(`${CONFIG.API_BASE_URL}/feedback`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        console.log('Ответ сервера:', response.status, response.statusText);
        
        if (response.ok) {
            // Скрываем форму и показываем сообщение об успехе с задержкой для плавности
            setTimeout(() => {
                feedbackForm.classList.add('hidden');
                feedbackSuccess.classList.remove('hidden');
                
                // Запускаем конфетти анимацию
                triggerConfettiAnimation();
            }, 300);
            
            // Очищаем поле ввода
            feedbackInput.value = '';
            
        } else {
            // Получаем детали ошибки от сервера
            let errorMessage = `Ошибка ${response.status}. Попробуйте снова.`;
            try {
                const errorData = await response.json();
                console.log('Детали ошибки:', errorData);
                errorMessage = errorData.error || errorMessage;
            } catch (parseError) {
                console.error('Не удалось распарсить ошибку:', parseError);
                const errorText = await response.text();
                console.log('Текст ошибки:', errorText);
            }
            throw new Error(errorMessage);
        }
    } catch (error) {
        console.error('Ошибка отправки обратной связи:', error);
        // Показываем конкретную ошибку, убедившись, что это строка
        const finalMessage = String(error.message || 'Произошла неизвестная ошибка. Пожалуйста, проверьте консоль.');
        safeAlert(finalMessage);
        
        // Встряхиваем кнопку при ошибке
        sendBtn.style.animation = 'shake 0.5s ease-in-out';
        setTimeout(() => {
            sendBtn.style.animation = '';
        }, 500);
        
    } finally {
        // Возвращаем кнопку в исходное состояние
        sendBtn.disabled = false;
        btnText.textContent = '📤 Отправить отзыв';
        spinner.classList.add('hidden');
        sendBtn.style.transform = '';
    }
}

// Анимация конфетти
function triggerConfettiAnimation() {
    const confettiElements = document.querySelectorAll('.confetti');
    confettiElements.forEach((confetti, index) => {
        confetti.style.animationDelay = `${index * 0.1}s`;
        confetti.style.animationDuration = `${2 + Math.random()}s`;
    });
}

// Сброс формы обратной связи к исходному состоянию
function resetFeedbackForm() {
    const feedbackInput = document.getElementById('feedback-input');
    const feedbackForm = document.querySelector('.feedback-form');
    const feedbackSuccess = document.getElementById('feedback-success');
    const charCounter = document.getElementById('char-counter');
    
    // Очищаем поле ввода
    if (feedbackInput) {
        feedbackInput.value = '';
        feedbackInput.placeholder = "Поделитесь своими мыслями о приложении, предложениями по улучшению или сообщите о проблемах...";
    }
    
    // Сбрасываем счетчик символов
    if (charCounter) {
        charCounter.textContent = '0/1000';
        charCounter.style.color = 'var(--tg-theme-hint-color)';
    }
    

    
    // Показываем форму и скрываем сообщение об успехе
    if (feedbackForm) {
        feedbackForm.classList.remove('hidden');
    }
    if (feedbackSuccess) {
        feedbackSuccess.classList.add('hidden');
    }
    
    // Фокусируемся на поле ввода
    if (feedbackInput) {
        setTimeout(() => {
            feedbackInput.focus();
        }, 100);
    }
}

// Инициализация формы обратной связи при загрузке экрана
function initFeedbackScreen() {
    initCharCounter();
    resetFeedbackForm();
}

function updateCharCounter() {
    const textarea = document.getElementById('feedback-input');
    const charCounter = document.getElementById('char-counter');
    
    if (textarea && charCounter) {
        const length = textarea.value.length;
        charCounter.textContent = `${length}/1000`;
        
        // Изменение цвета при приближении к лимиту
        if (length > 950) {
            charCounter.style.color = 'var(--danger-color)';
        } else if (length > 800) {
            charCounter.style.color = 'var(--warning-color)';
        } else {
            charCounter.style.color = 'var(--tg-theme-hint-color)';
        }
    }
}

// Показ скелетонов загрузки для вопросов
function showQuestionsLoadingSkeleton(container) {
    container.innerHTML = '';
    for (let i = 0; i < 5; i++) {
        const skeleton = document.createElement('div');
        skeleton.className = 'question-item';
        skeleton.innerHTML = `
            <div class="question-header">
                <div class="question-meta">
                    <div class="loading-skeleton" style="width: 2rem; height: 2rem; border-radius: 50%;"></div>
                    <div class="loading-skeleton title"></div>
                </div>
                <div class="loading-skeleton date"></div>
            </div>
            <div class="loading-skeleton text"></div>
            <div class="loading-skeleton text" style="width: 60%;"></div>
        `;
        container.appendChild(skeleton);
    }
}

// Показ скелетонов загрузки для истории
function showHistoryLoadingSkeleton(container) {
    container.innerHTML = '';
    for (let i = 0; i < 3; i++) {
        const skeleton = document.createElement('div');
        skeleton.className = 'history-item';
        skeleton.innerHTML = `
            <div class="history-header">
                <div class="history-meta">
                    <div class="loading-skeleton" style="width: 2rem; height: 2rem; border-radius: 50%;"></div>
                    <div class="loading-skeleton title"></div>
                </div>
            </div>
            <div class="loading-skeleton text"></div>
            <div class="loading-skeleton text" style="width: 80%;"></div>
        `;
        container.appendChild(skeleton);
    }
} 