// Telegram Web App API
let tg = window.Telegram.WebApp;

// Конфигурация
const CONFIG = {
    API_BASE_URL: window.location.origin + '/api', // Будет работать с /var/www/html/api
    WEBSOCKET_URL: 'ws://213.171.25.85:8000/ws'
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

// Глобальные переменные для ролей и специализаций
let roles = [];
let specializations = [];

// Инициализация приложения
document.addEventListener('DOMContentLoaded', async function() {
    initViewportFixes();
    initTelegramWebApp();
    await loadRolesAndSpecializations();
    await loadUserProfile();
    await loadHistory();
    await loadQuestions();
    createMainMenu();
});

// Исправления для viewport на разных устройствах
function initViewportFixes() {
    function setVhProperty() {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
    }
    
    setVhProperty();
    
    window.addEventListener('resize', debounce(setVhProperty, 100));
    window.addEventListener('orientationchange', () => {
        setTimeout(setVhProperty, 100);
    });
    
    let lastTouchEnd = 0;
    document.addEventListener('touchend', function (event) {
        const now = (new Date()).getTime();
        if (now - lastTouchEnd <= 300) {
            event.preventDefault();
        }
        lastTouchEnd = now;
    }, false);
}

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

// Инициализация Telegram WebApp
function initTelegramWebApp() {
    try {
        tg.expand();
        tg.setHeaderColor('bg_color');
        
        if (tg.initDataUnsafe && tg.initDataUnsafe.user) {
            AppState.user = tg.initDataUnsafe.user;
            console.log('Пользователь Telegram:', AppState.user);
        }
        
        tg.MainButton.text = 'Готово';
        tg.MainButton.hide();
        
        tg.BackButton.onClick(() => {
            goBack();
        });
        
        console.log('Telegram Web App инициализирован');
    } catch (error) {
        console.error('Ошибка инициализации Telegram Web App:', error);
    }
}

// Инициализация Telegram UI Kit
function initTelegramUI() {
    if (!TelegramUI) {
        console.error('Telegram UI Kit не загружен');
        return;
    }

    // Создаем главное меню
    createMainMenu();
    
    console.log('Telegram UI Kit инициализирован');
}

// Создание главного меню с Telegram UI компонентами
function createMainMenu() {
    const menuGrid = document.getElementById('menu-grid');
    if (!menuGrid) return;

    const menuItems = [
        {
            id: 'ask-question',
            icon: '❓',
            title: 'Задать вопрос',
            description: 'Получите персонализированный ответ от AI-ментора'
        },
        {
            id: 'questions-library',
            icon: '📚',
            title: 'Библиотека вопросов',
            description: 'Готовые вопросы по ролям и специализациям'
        },
        {
            id: 'history',
            icon: '📜',
            title: 'История диалогов',
            description: 'Просмотрите предыдущие беседы'
        },
        {
            id: 'profile',
            icon: '👤',
            title: 'Профиль',
            description: 'Настройте роль и специализацию'
        },
        {
            id: 'feedback',
            icon: '💬',
            title: 'Обратная связь',
            description: 'Поделитесь предложениями по улучшению'
        }
    ];

    menuGrid.innerHTML = '';

    menuItems.forEach(item => {
        const card = createMenuCard(item);
        menuGrid.appendChild(card);
    });
}

// Создание карточки меню с использованием Telegram UI
function createMenuCard(item) {
    const card = document.createElement('div');
    card.className = 'menu-card';
    card.onclick = () => showScreen(item.id);
    
    // Используем стили Telegram UI
    card.style.cssText = `
        background: var(--tg-theme-secondary-bg-color, #f0f0f0);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        min-height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        border: 1px solid var(--tg-theme-section-separator-color, #e0e0e0);
    `;

    card.innerHTML = `
        <div class="menu-icon">${item.icon}</div>
        <h3 style="color: var(--tg-theme-text-color); font-size: 16px; font-weight: 600; margin-bottom: 4px;">
            ${item.title}
        </h3>
        <p style="color: var(--tg-theme-hint-color); font-size: 14px; line-height: 1.3;">
            ${item.description}
        </p>
    `;

    return card;
}

// Создание заголовка экрана с кнопкой назад
function createScreenHeader(title, showBackButton = true) {
    const header = document.createElement('div');
    header.style.cssText = `
        display: flex;
        align-items: center;
        justify-content: ${showBackButton ? 'flex-start' : 'center'};
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--tg-theme-section-separator-color, #e0e0e0);
        position: relative;
    `;

    if (showBackButton) {
        const backButton = document.createElement('button');
        backButton.innerHTML = 'Назад';
        backButton.style.cssText = `
            background: var(--tg-theme-bg-color);
            border: none;
            border-radius: 12px;
            padding: 8px 16px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--tg-theme-button-color);
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.15s cubic-bezier(0.4, 0.0, 0.2, 1);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            position: relative;
            overflow: hidden;
            white-space: nowrap;
        `;
        
        // Создаем ripple эффект
        backButton.addEventListener('mousedown', (e) => {
            backButton.style.transform = 'scale(0.92)';
            backButton.style.boxShadow = '0 1px 4px rgba(0, 0, 0, 0.15)';
            
            // Ripple эффект
            const ripple = document.createElement('div');
            const rect = backButton.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;
            
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: var(--tg-theme-button-color);
                border-radius: 12px;
                opacity: 0.1;
                transform: scale(0);
                animation: ripple 0.6s linear;
                pointer-events: none;
            `;
            
            backButton.appendChild(ripple);
            
            setTimeout(() => {
                if (ripple.parentNode) {
                    ripple.parentNode.removeChild(ripple);
                }
            }, 600);
        });
        
        backButton.addEventListener('mouseup', () => {
            backButton.style.transform = 'scale(1)';
            backButton.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.1)';
        });
        
        backButton.addEventListener('mouseleave', () => {
            backButton.style.transform = 'scale(1)';
            backButton.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.1)';
        });
        
        // Hover эффект
        backButton.addEventListener('mouseenter', () => {
            backButton.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
        });
        
        backButton.onclick = () => showScreen('main-menu');
        header.appendChild(backButton);
    }

    const titleElement = document.createElement('h2');
    titleElement.textContent = title;
    titleElement.style.cssText = `
        color: var(--tg-theme-text-color);
        font-size: 20px;
        font-weight: 600;
        margin: 0;
        ${showBackButton ? 'position: absolute; left: 50%; transform: translateX(-50%);' : ''}
    `;
    
    header.appendChild(titleElement);

    return header;
}

// Создание кнопки в стиле Telegram
function createButton(text, mode = 'primary', onClick = null, disabled = false) {
    const button = document.createElement('button');
    button.textContent = text;
    button.disabled = disabled;
    
    const isPrimary = mode === 'primary';
    
    button.style.cssText = `
        background: ${isPrimary ? 'var(--tg-theme-button-color, #0088cc)' : 'transparent'};
        color: ${isPrimary ? 'var(--tg-theme-button-text-color, #ffffff)' : 'var(--tg-theme-button-color, #0088cc)'};
        border: ${isPrimary ? 'none' : '1px solid var(--tg-theme-button-color, #0088cc)'};
        border-radius: 8px;
        padding: 12px 24px;
        font-size: 16px;
        font-weight: 500;
        cursor: ${disabled ? 'not-allowed' : 'pointer'};
        transition: all 0.2s ease;
        min-height: 44px;
        display: flex;
        align-items: center;
        justify-content: center;
        opacity: ${disabled ? '0.6' : '1'};
    `;

    if (onClick && !disabled) {
        button.onclick = onClick;
    }

    // Добавляем hover эффект
    if (!disabled) {
        button.addEventListener('mousedown', () => {
            button.style.transform = 'scale(0.98)';
        });
        
        button.addEventListener('mouseup', () => {
            button.style.transform = 'scale(1)';
        });
        
        button.addEventListener('mouseleave', () => {
            button.style.transform = 'scale(1)';
        });
    }

    return button;
}

// Создание текстового поля в стиле Telegram
function createTextarea(placeholder = '', rows = 4) {
    const textarea = document.createElement('textarea');
    textarea.placeholder = placeholder;
    textarea.rows = rows;
    
    textarea.style.cssText = `
        width: 100%;
        background: var(--tg-theme-secondary-bg-color, #f0f0f0);
        border: 1px solid var(--tg-theme-section-separator-color, #e0e0e0);
        border-radius: 8px;
        padding: 12px;
        font-size: 16px;
        color: var(--tg-theme-text-color);
        resize: vertical;
        min-height: 100px;
        font-family: inherit;
        line-height: 1.4;
    `;
    
    // Фокус стили
    textarea.addEventListener('focus', () => {
        textarea.style.borderColor = 'var(--tg-theme-button-color, #0088cc)';
        textarea.style.outline = 'none';
    });
    
    textarea.addEventListener('blur', () => {
        textarea.style.borderColor = 'var(--tg-theme-section-separator-color, #e0e0e0)';
    });

    return textarea;
}

// Создание карточки в стиле Telegram
function createCard(content) {
    const card = document.createElement('div');
    card.style.cssText = `
        background: var(--tg-theme-secondary-bg-color, #f0f0f0);
        border-radius: 12px;
        padding: 16px;
        border: 1px solid var(--tg-theme-section-separator-color, #e0e0e0);
        margin-bottom: 12px;
    `;
    
    if (typeof content === 'string') {
        card.innerHTML = content;
    } else {
        card.appendChild(content);
    }
    
    return card;
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
    if (!tg) return;
    
    if (screenId === 'main-menu') {
        tg.BackButton.hide();
    } else {
        tg.BackButton.show();
    }
}

// Возврат назад
function goBack() {
    if (AppState.currentScreen === 'main-menu') {
        if (tg) tg.close();
    } else {
        showScreen('main-menu');
    }
}

// Загрузка данных для экрана
async function loadScreenData(screenId) {
    switch (screenId) {
        case 'ask-question':
            createQuestionScreen();
            // Загружаем историю для отображения предыдущих вопросов при необходимости
            await loadHistory();
            break;
        case 'questions-library':
            createQuestionsLibraryScreen();
            await loadQuestions(); // Перезагружаем вопросы с учетом текущего профиля
            renderQuestions();
            break;
        case 'history':
            await loadHistory();
            createHistoryScreen();
            renderHistory();
            break;
        case 'profile':
            createProfileScreen();
            renderProfile();
            break;
        case 'feedback':
            createFeedbackScreen();
            initFeedbackScreen();
            break;
    }
}

// Загрузка контента для экрана (старая функция для совместимости)
function loadScreenContent(screenId) {
    return loadScreenData(screenId);
}

// Создание экрана вопросов
function createQuestionScreen() {
    const header = document.getElementById('question-header');
    const formContainer = document.getElementById('question-form-container');
    
    if (!header || !formContainer) return;
    
    // Заголовок
    header.innerHTML = '';
    header.appendChild(createScreenHeader('Задать вопрос'));
    
    // Форма
    formContainer.innerHTML = '';
    
    const form = document.createElement('div');
    form.className = 'question-form';
    
    const label = document.createElement('label');
    label.textContent = 'Ваш вопрос:';
    label.style.cssText = `
        color: var(--tg-theme-text-color);
        font-weight: 500;
        margin-bottom: 8px;
        display: block;
    `;
    
    const textarea = createTextarea('Опишите вашу ситуацию или задайте вопрос...');
    textarea.id = 'question-input';
    
    const sendButton = createButton('Отправить', 'primary', sendQuestion);
    sendButton.id = 'send-question';
    
    form.appendChild(label);
    form.appendChild(textarea);
    form.appendChild(sendButton);
    
    formContainer.appendChild(form);
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

// Отображение вопросов
function renderQuestions() {
    const questionsList = document.getElementById('questions-list');
    const questions = AppState.questions || [];
    
    if (!questionsList) return;
    
    // Показываем скелетон при загрузке
    if (questions.length === 0 && AppState.questions === null) {
        showQuestionsLoadingSkeleton(questionsList);
        return;
    }
    
    questionsList.innerHTML = '';
    
    if (questions.length === 0) {
        const emptyState = document.createElement('div');
        emptyState.className = 'empty-state';
        emptyState.style.cssText = `
            text-align: center;
            padding: 40px 20px;
            color: var(--tg-theme-hint-color);
        `;
        emptyState.innerHTML = `
            <div style="font-size: 48px; margin-bottom: 16px;">📝</div>
            <h3 style="margin: 0 0 8px 0; font-size: 18px; font-weight: 600; color: var(--tg-theme-text-color);">Вопросы не найдены</h3>
            <p style="margin: 0; font-size: 14px; line-height: 1.5;">Заполните профиль для получения персонализированных вопросов</p>
        `;
        questionsList.appendChild(emptyState);
        return;
    }
    
    questions.forEach((question, index) => {
        const div = document.createElement('div');
        div.className = 'question-item';
        div.style.cssText = `
            background: var(--tg-theme-secondary-bg-color);
            border: 1px solid var(--tg-theme-section-separator-color);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            cursor: pointer;
            transition: transform 0.2s ease;
        `;
        
        const preview = question.preview || question.text.substring(0, 120) + '...';
        
        div.innerHTML = `
            <div class="question-header" style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <div class="question-meta" style="display: flex; align-items: center;">
                    <div class="question-icon" style="margin-right: 8px; font-size: 20px;">${getCategoryIcon(question.category)}</div>
                    <div class="question-title" style="font-weight: 600; color: var(--tg-theme-text-color); font-size: 16px;">${question.title || 'Вопрос'}</div>
                </div>
                <div class="question-category" style="background: var(--tg-theme-button-color); color: var(--tg-theme-button-text-color); padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 500;">${getCategoryName(question.category)}</div>
            </div>
            <div class="question-preview" style="color: var(--tg-theme-text-color); font-size: 14px; line-height: 1.4;">${preview}</div>
        `;
        
        div.addEventListener('mousedown', () => {
            div.style.transform = 'scale(0.98)';
        });
        
        div.addEventListener('mouseup', () => {
            div.style.transform = 'scale(1)';
        });
        
        div.addEventListener('mouseleave', () => {
            div.style.transform = 'scale(1)';
        });
        
        div.onclick = async () => await useQuestionDirectly(index);
        questionsList.appendChild(div);
    });
}

// Использование вопроса из библиотеки
async function useQuestionDirectly(index) {
    const questions = AppState.questions || [];
    const question = questions[index];
    
    if (!question) {
        showAlert('Вопрос не найден');
        return;
    }
    
    // Показываем заданный вопрос
    displayAskedQuestion(question.text);
    
    // Сохраняем вопрос для генерации связанных вопросов
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
                question_id: question.id,
                user_id: userId,
                role: AppState.profile.role,
                specialization: AppState.profile.specialization
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            await displayAnswer(question.text, data.answer);
            
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
            
            // Предыдущие вопросы будут показаны в displayAnswer
        } else {
            throw new Error('Ошибка получения ответа');
        }
    } catch (error) {
        console.error('Ошибка отправки библиотечного вопроса:', error);
        showAlert('Ошибка получения ответа. Попробуйте снова.');
    } finally {
        hideLoader();
    }
}

// Создание экрана библиотеки вопросов
function createQuestionsLibraryScreen() {
    const header = document.getElementById('library-header');
    const questionsList = document.getElementById('questions-list');
    
    if (!header || !questionsList) return;
    
    header.innerHTML = '';
    header.appendChild(createScreenHeader('Библиотека вопросов'));
    
    questionsList.innerHTML = '<p style="color: var(--tg-theme-hint-color); text-align: center; padding: 20px;">Загрузка вопросов...</p>';
    
    // Рендерим вопросы
    setTimeout(() => {
        renderQuestions();
    }, 100);
}

// Отображение истории
function renderHistory() {
    const historyList = document.getElementById('history-list');
    
    if (!historyList) return;
    
    // Показываем скелетон при загрузке
    if (AppState.history.length === 0 && AppState.history === null) {
        showHistoryLoadingSkeleton(historyList);
        return;
    }
    
    historyList.innerHTML = '';
    
    console.log('Рендерим историю, количество элементов:', AppState.history.length);
    
    if (AppState.history.length === 0) {
        const emptyState = document.createElement('div');
        emptyState.style.cssText = `
            text-align: center;
            padding: 40px 20px;
            color: var(--tg-theme-hint-color);
        `;
        emptyState.innerHTML = `
            <div style="font-size: 48px; margin-bottom: 16px;">📜</div>
            <h3 style="margin: 0 0 8px 0; font-size: 18px; font-weight: 600; color: var(--tg-theme-text-color);">История пуста</h3>
            <p style="margin: 0; font-size: 14px; line-height: 1.5;">Задайте первый вопрос, чтобы начать</p>
        `;
        historyList.appendChild(emptyState);
        return;
    }
    
    AppState.history.forEach((item, index) => {
        const div = document.createElement('div');
        div.className = 'history-item';
        div.style.cssText = `
            background: var(--tg-theme-secondary-bg-color);
            border: 1px solid var(--tg-theme-section-separator-color);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            cursor: pointer;
            transition: transform 0.2s ease;
        `;
        
        const date = new Date(item.timestamp).toLocaleDateString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
        
        const questionPreview = item.question.length > 80 ? 
            item.question.substring(0, 80) + '...' : 
            item.question;
            
        const answerPreview = item.answer.replace(/<[^>]*>/g, ''); // Убираем HTML теги
        const shortAnswer = answerPreview.length > 100 ? 
            answerPreview.substring(0, 100) + '...' : 
            answerPreview;
        
        div.innerHTML = `
            <div class="history-header" style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <div class="history-date" style="color: var(--tg-theme-hint-color); font-size: 12px;">${date}</div>
            </div>
            <div class="history-question" style="color: var(--tg-theme-text-color); font-weight: 600; font-size: 14px; margin-bottom: 8px;">${questionPreview}</div>
            <div class="history-answer" style="color: var(--tg-theme-hint-color); font-size: 13px; line-height: 1.4;">${shortAnswer}</div>
        `;
        
        div.addEventListener('mousedown', () => {
            div.style.transform = 'scale(0.98)';
        });
        
        div.addEventListener('mouseup', () => {
            div.style.transform = 'scale(1)';
        });
        
        div.addEventListener('mouseleave', () => {
            div.style.transform = 'scale(1)';
        });
        
        div.onclick = () => showHistoryDetail(item);
        historyList.appendChild(div);
    });
}

// Показать детали истории
function showHistoryDetail(item) {
    // Создаем модальное окно
    let modal = document.getElementById('history-modal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'history-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            padding: 20px;
        `;
        document.body.appendChild(modal);
    }
    
    const date = new Date(item.timestamp).toLocaleDateString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
    
    modal.innerHTML = `
        <div class="modal-content" style="
            background: var(--tg-theme-bg-color);
            border-radius: 16px;
            max-width: 90%;
            max-height: 80%;
            overflow-y: auto;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        ">
            <div class="modal-header" style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 20px 20px 16px 20px;
                border-bottom: 1px solid var(--tg-theme-section-separator-color);
            ">
                <h3 style="margin: 0; color: var(--tg-theme-text-color); font-size: 18px; font-weight: 600;">Детали диалога</h3>
                <button class="close-btn" onclick="closeHistoryModal()" style="
                    background: none;
                    border: none;
                    font-size: 24px;
                    color: var(--tg-theme-hint-color);
                    cursor: pointer;
                    padding: 0;
                    width: 32px;
                    height: 32px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    border-radius: 50%;
                ">×</button>
            </div>
            <div class="modal-body" style="padding: 20px;">
                <div class="history-detail-meta" style="
                    display: flex;
                    justify-content: flex-end;
                    align-items: center;
                    margin-bottom: 16px;
                    padding: 12px;
                    background: var(--tg-theme-secondary-bg-color);
                    border-radius: 8px;
                ">
                    <span style="color: var(--tg-theme-hint-color); font-size: 14px;">${date}</span>
                </div>
                
                <div class="history-detail-question" style="margin-bottom: 20px;">
                    <h4 style="color: var(--tg-theme-text-color); margin-bottom: 8px; font-size: 16px; font-weight: 600;">Вопрос:</h4>
                    <div style="
                        background: var(--tg-theme-secondary-bg-color);
                        padding: 12px;
                        border-radius: 8px;
                        color: var(--tg-theme-text-color);
                        line-height: 1.5;
                    ">${item.question}</div>
                </div>
                
                <div class="history-detail-answer">
                    <h4 style="color: var(--tg-theme-text-color); margin-bottom: 8px; font-size: 16px; font-weight: 600;">Ответ:</h4>
                    <div style="
                        background: var(--tg-theme-secondary-bg-color);
                        padding: 12px;
                        border-radius: 8px;
                        color: var(--tg-theme-text-color);
                        line-height: 1.6;
                    " class="answer-text">${convertMarkdownToHtml(formatAnswerText(item.answer))}</div>
                </div>
            </div>
        </div>
    `;
    
    modal.style.display = 'flex';
    
    // Закрытие по клику на фон
    modal.onclick = (e) => {
        if (e.target === modal) {
            closeHistoryModal();
        }
    };
}

// Закрыть модальное окно истории
function closeHistoryModal() {
    const modal = document.getElementById('history-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Очистка истории
async function clearHistory() {
    // Показываем кастомное подтверждение
    showConfirmationModal(
        'Очистить историю?',
        'Это действие удалит все ваши предыдущие диалоги без возможности восстановления.',
        async () => {
            try {
                showLoader();
                const userId = AppState.user?.id || 'guest';
                const response = await fetch(`${CONFIG.API_BASE_URL}/history/${userId}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    AppState.history = [];
                    renderHistory();
                    showAlert('История очищена');
                } else {
                    throw new Error('Ошибка очистки истории');
                }
            } catch (error) {
                console.error('Ошибка очистки истории:', error);
                showAlert('Ошибка очистки истории');
            } finally {
                hideLoader();
            }
        }
    );
}

// Создание экрана истории
function createHistoryScreen() {
    const header = document.getElementById('history-header');
    const historyList = document.getElementById('history-list');
    
    if (!header || !historyList) return;
    
    header.innerHTML = '';
    const headerElement = createScreenHeader('История диалогов');
    
    // Добавляем кнопку очистки
    const clearButton = createButton('Очистить', 'secondary', clearHistory);
    clearButton.style.cssText += 'margin-left: auto; padding: 8px 16px; font-size: 14px;';
    headerElement.appendChild(clearButton);
    
    header.appendChild(headerElement);
    
    historyList.innerHTML = '<p style="color: var(--tg-theme-hint-color); text-align: center; padding: 20px;">Загрузка истории...</p>';
    
    // Рендерим историю
    setTimeout(() => {
        renderHistory();
    }, 100);
}

// Обновление специализаций при выборе роли
function updateSpecializations() {
    const roleSelect = document.getElementById('role-select');
    const specializationSelect = document.getElementById('specialization-select');
    
    if (!roleSelect || !specializationSelect) return;
    
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
    
    if (!profileName || !profileStatus) return;
    
    const roleSelect = document.getElementById('role-select');
    const specializationSelect = document.getElementById('specialization-select');
    
    if (roleSelect) AppState.profile.role = roleSelect.value;
    if (specializationSelect) AppState.profile.specialization = specializationSelect.value;
    
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
    
    if (!roleSelect || !specializationSelect) return;
    
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
        updateSpecializations();
        updateProfileInfo();
    });
    
    specializationSelect.addEventListener('change', async function() {
        AppState.profile.specialization = this.value;
        updateProfileInfo();
        // Перезагружаем вопросы при изменении специализации
        if (AppState.profile.role && AppState.profile.specialization) {
            await loadQuestions();
        }
    });
    
    // Обновляем информацию о профиле
    updateProfileInfo();
}

// Сохранение профиля
async function saveProfile() {
    const roleSelect = document.getElementById('role-select');
    const specializationSelect = document.getElementById('specialization-select');
    
    if (!roleSelect || !specializationSelect) return;
    
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

// Создание экрана профиля
function createProfileScreen() {
    const header = document.getElementById('profile-header');
    const profileContent = document.getElementById('profile-content');
    
    if (!header || !profileContent) return;
    
    header.innerHTML = '';
    header.appendChild(createScreenHeader('Профиль'));
    
    // Создаем содержимое профиля
    profileContent.innerHTML = `
        <!-- Информация о пользователе -->
        <div class="profile-info" style="display: flex; align-items: center; margin-bottom: 24px; padding: 16px; background: var(--tg-theme-secondary-bg-color); border-radius: 12px;">
            <div class="profile-avatar" style="margin-right: 16px;">
                <div class="avatar-placeholder" style="width: 60px; height: 60px; background: var(--tg-theme-button-color); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24px;">👤</div>
            </div>
            <div class="profile-details">
                <h3 id="profile-name" style="color: var(--tg-theme-text-color); margin: 0 0 4px 0; font-size: 18px; font-weight: 600;">Настройка профиля</h3>
                <p id="profile-status" style="color: var(--tg-theme-hint-color); margin: 0; font-size: 14px;">Заполните информацию о себе</p>
            </div>
        </div>

        <!-- Форма профиля -->
        <div class="profile-form">
            <div class="form-section" style="margin-bottom: 24px;">
                <h4 style="color: var(--tg-theme-text-color); margin-bottom: 8px;">Роль в команде</h4>
                <div class="select-wrapper" style="position: relative;">
                    <select id="role-select" onchange="updateSpecializations()" style="width: 100%; padding: 12px; border: 1px solid var(--tg-theme-section-separator-color); border-radius: 8px; background: var(--tg-theme-secondary-bg-color); color: var(--tg-theme-text-color); font-size: 16px; appearance: none;">
                        <option value="">Выберите вашу роль</option>
                    </select>
                    <div class="select-icon" style="position: absolute; right: 12px; top: 50%; transform: translateY(-50%); pointer-events: none; color: var(--tg-theme-hint-color);">▼</div>
                </div>
                <p class="field-description" style="color: var(--tg-theme-hint-color); font-size: 12px; margin-top: 4px;">Выберите роль, которая лучше всего описывает вашу должность</p>
            </div>
            
            <div class="form-section" style="margin-bottom: 24px;">
                <h4 style="color: var(--tg-theme-text-color); margin-bottom: 8px;">Специализация</h4>
                <div class="select-wrapper" style="position: relative;">
                    <select id="specialization-select" style="width: 100%; padding: 12px; border: 1px solid var(--tg-theme-section-separator-color); border-radius: 8px; background: var(--tg-theme-secondary-bg-color); color: var(--tg-theme-text-color); font-size: 16px; appearance: none;">
                        <option value="">Сначала выберите роль</option>
                    </select>
                    <div class="select-icon" style="position: absolute; right: 12px; top: 50%; transform: translateY(-50%); pointer-events: none; color: var(--tg-theme-hint-color);">▼</div>
                </div>
                <p class="field-description" style="color: var(--tg-theme-hint-color); font-size: 12px; margin-top: 4px;">Укажите вашу техническую специализацию</p>
            </div>
        </div>
        
        <div class="profile-actions">
            <button class="primary-btn full-width" onclick="saveProfile()" style="width: 100%; padding: 16px; background: var(--tg-theme-button-color); color: var(--tg-theme-button-text-color); border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer;">
                <span class="btn-icon">💾</span>
                Сохранить профиль
            </button>
        </div>
    `;
    
    // Рендерим профиль после создания элементов
    setTimeout(() => {
        renderProfile();
    }, 100);
}

// Инициализация счетчика символов
function initCharCounter() {
    const textarea = document.getElementById('feedback-input');
    if (textarea) {
        updateCharCounter();
    }
}

// Обновление счетчика символов
function updateCharCounter() {
    const textarea = document.getElementById('feedback-input');
    const charCounter = document.getElementById('char-counter');
    
    if (textarea && charCounter) {
        const length = textarea.value.length;
        const maxLength = 1000;
        
        charCounter.textContent = `${length}/${maxLength}`;
        
        if (length > maxLength * 0.9) {
            charCounter.style.color = 'var(--tg-theme-destructive-text-color, #ff4444)';
        } else if (length > maxLength * 0.7) {
            charCounter.style.color = 'var(--tg-theme-accent-text-color, #ff8800)';
        } else {
            charCounter.style.color = 'var(--tg-theme-hint-color)';
        }
    }
}

// Безопасный alert
function safeAlert(msg) {
    try {
        if (tg && typeof tg.showAlert === 'function') {
            tg.showAlert(String(msg));
        } else {
            alert(String(msg));
        }
    } catch (error) {
        console.error('Ошибка показа уведомления:', error);
        console.log('Сообщение:', msg);
    }
}

// Отправка обратной связи
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
    if (spinner) spinner.classList.remove('hidden');
    
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
            // Скрываем форму и показываем сообщение об успехе
            setTimeout(() => {
                if (feedbackForm) feedbackForm.classList.add('hidden');
                if (feedbackSuccess) feedbackSuccess.classList.remove('hidden');
                
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
        if (spinner) spinner.classList.add('hidden');
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

// Сброс формы обратной связи
function resetFeedbackForm() {
    const feedbackInput = document.getElementById('feedback-input');
    const feedbackForm = document.querySelector('.feedback-form');
    const feedbackSuccess = document.getElementById('feedback-success');
    const charCounter = document.getElementById('char-counter');
    
    if (feedbackInput) {
        feedbackInput.value = '';
    }
    
    if (charCounter) {
        charCounter.textContent = '0/1000';
        charCounter.style.color = 'var(--tg-theme-hint-color)';
    }
    
    if (feedbackForm) {
        feedbackForm.classList.remove('hidden');
    }
    if (feedbackSuccess) {
        feedbackSuccess.classList.add('hidden');
    }
    
    if (feedbackInput) {
        setTimeout(() => {
            feedbackInput.focus();
        }, 100);
    }
}

// Инициализация экрана обратной связи
function initFeedbackScreen() {
    initCharCounter();
    resetFeedbackForm();
}

// Создание экрана обратной связи
function createFeedbackScreen() {
    const header = document.getElementById('feedback-header');
    const feedbackContent = document.getElementById('feedback-content');
    
    if (!header || !feedbackContent) return;
    
    header.innerHTML = '';
    header.appendChild(createScreenHeader('Обратная связь'));
    
    // Создаем содержимое обратной связи
    feedbackContent.innerHTML = `
        <!-- Информационная секция -->
        <div class="feedback-hero" style="text-align: center; margin-bottom: 24px; padding: 20px; background: var(--tg-theme-secondary-bg-color); border-radius: 12px;">
            <div class="feedback-icon-large" style="font-size: 48px; margin-bottom: 12px;">💬</div>
            <h3 style="color: var(--tg-theme-text-color); margin: 0 0 8px 0; font-size: 20px; font-weight: 600;">Поделитесь своим мнением</h3>
            <p style="color: var(--tg-theme-hint-color); margin: 0; font-size: 14px; line-height: 1.5;">Ваши отзывы и предложения помогают нам делать GigaMentor лучше каждый день!</p>
        </div>

        <!-- Форма обратной связи -->
        <div class="feedback-form">
            <div class="input-group" style="margin-bottom: 16px;">
                <label for="feedback-input" style="display: block; color: var(--tg-theme-text-color); font-weight: 500; margin-bottom: 8px;">
                    <span class="label-text">Ваш отзыв или предложение</span>
                </label>
                <div class="textarea-wrapper" style="position: relative;">
                    <textarea 
                        id="feedback-input" 
                        placeholder="Поделитесь своими мыслями о приложении, предложениями по улучшению или сообщите о проблемах..."
                        maxlength="1000"
                        oninput="updateCharCounter()"
                        style="
                            width: 100%;
                            min-height: 120px;
                            background: var(--tg-theme-secondary-bg-color);
                            border: 1px solid var(--tg-theme-section-separator-color);
                            border-radius: 8px;
                            padding: 12px;
                            font-size: 16px;
                            color: var(--tg-theme-text-color);
                            resize: vertical;
                            font-family: inherit;
                            line-height: 1.4;
                        "
                    ></textarea>
                    <div id="char-counter" class="char-counter" style="
                        position: absolute;
                        bottom: 8px;
                        right: 12px;
                        font-size: 12px;
                        color: var(--tg-theme-hint-color);
                        background: var(--tg-theme-bg-color);
                        padding: 2px 4px;
                        border-radius: 4px;
                    ">0/1000</div>
                </div>
            </div>
            
            <button id="feedback-submit-btn" class="primary-btn full-width" onclick="sendFeedback()" style="
                width: 100%;
                padding: 16px;
                background: var(--tg-theme-button-color);
                color: var(--tg-theme-button-text-color);
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            ">
                <span class="btn-text">📤 Отправить отзыв</span>
                <div class="spinner hidden" style="width: 16px; height: 16px;"></div>
            </button>
        </div>

        <!-- Сообщение об успехе -->
        <div id="feedback-success" class="feedback-success hidden" style="text-align: center; padding: 40px 20px;">
            <div class="success-animation" style="position: relative; margin-bottom: 20px;">
                <div class="success-icon" style="font-size: 64px; margin-bottom: 16px;">🎉</div>
                <div class="success-confetti" style="position: absolute; top: 0; left: 50%; transform: translateX(-50%); width: 100px; height: 100px; pointer-events: none;">
                    <div class="confetti" style="position: absolute; width: 10px; height: 10px; background: #ff6b6b; animation: confetti-fall 3s ease-out infinite;"></div>
                    <div class="confetti" style="position: absolute; width: 10px; height: 10px; background: #4ecdc4; animation: confetti-fall 3s ease-out infinite;"></div>
                    <div class="confetti" style="position: absolute; width: 10px; height: 10px; background: #45b7d1; animation: confetti-fall 3s ease-out infinite;"></div>
                    <div class="confetti" style="position: absolute; width: 10px; height: 10px; background: #f9ca24; animation: confetti-fall 3s ease-out infinite;"></div>
                    <div class="confetti" style="position: absolute; width: 10px; height: 10px; background: #6c5ce7; animation: confetti-fall 3s ease-out infinite;"></div>
                </div>
            </div>
            <h3 style="color: var(--tg-theme-text-color); margin: 0 0 8px 0; font-size: 20px; font-weight: 600;">Спасибо за отзыв!</h3>
            <p style="color: var(--tg-theme-hint-color); margin: 0 0 20px 0; font-size: 14px; line-height: 1.5;">Ваше мнение очень важно для нас. Мы обязательно рассмотрим ваши предложения.</p>
            <div class="success-actions" style="display: flex; gap: 12px; justify-content: center;">
                <button class="primary-btn" onclick="resetFeedbackForm()" style="
                    padding: 12px 20px;
                    background: var(--tg-theme-button-color);
                    color: var(--tg-theme-button-text-color);
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
                ">
                    <span>✨ Оставить еще отзыв</span>
                </button>
                <button class="secondary-btn" onclick="showScreen('main-menu')" style="
                    padding: 12px 20px;
                    background: transparent;
                    color: var(--tg-theme-button-color);
                    border: 1px solid var(--tg-theme-button-color);
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: 500;
                    cursor: pointer;
                ">
                    <span>🏠 В главное меню</span>
                </button>
            </div>
        </div>
    `;
    
    // Инициализируем экран обратной связи
    setTimeout(() => {
        initFeedbackScreen();
    }, 100);
}

// Отображение заданного вопроса
function displayAskedQuestion(question) {
    const askedQuestionContainer = document.getElementById('asked-question-container');
    const askedQuestionText = document.getElementById('asked-question-text');
    
    if (askedQuestionContainer && askedQuestionText) {
        askedQuestionText.textContent = question;
        askedQuestionContainer.classList.remove('hidden');
    }
}

// Отправка вопроса
async function sendQuestion() {
    const questionInput = document.getElementById('question-input');
    const sendBtn = document.getElementById('send-question');
    
    if (!questionInput || !sendBtn) return;
    
    const question = questionInput.value.trim();
    if (!question) {
        showAlert('Пожалуйста, введите ваш вопрос');
        return;
    }
    
    const userId = AppState.user?.id || 'guest';
    
    // Показываем заданный вопрос
    displayAskedQuestion(question);
    
    // Показываем полноэкранный лоадер
    showLoader();
    
    // Блокируем кнопку и показываем спиннер
    sendBtn.disabled = true;
    const btnText = sendBtn.querySelector('.btn-text') || sendBtn;
    const spinner = sendBtn.querySelector('.spinner');
    
    btnText.textContent = 'Отправляем...';
    if (spinner) spinner.classList.remove('hidden');
    
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/ask`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                question: question,
                user_id: userId,
                role: AppState.profile.role,
                specialization: AppState.profile.specialization
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            
            // Отображаем ответ и запускаем генерацию связанных вопросов
            await displayAnswer(question, data.answer);
            
            // Добавляем в локальную историю
            AppState.history.unshift({
                id: Date.now(),
                question: question,
                answer: data.answer,
                timestamp: new Date(),
                role: AppState.profile.role,
                specialization: AppState.profile.specialization
            });
            
            // Перезагружаем историю из БД с задержкой
            setTimeout(async () => {
                await loadHistory();
                console.log('✅ История обновлена из БД');
            }, 500);
            
            // Очищаем поле ввода
            questionInput.value = '';
            
            // Предыдущие вопросы будут показаны в displayAnswer
            
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
        if (spinner) spinner.classList.add('hidden');
    }
}

// Форматирование ответа с улучшенной пунктуацией
function formatAnswerText(text) {
    if (!text) return '';
    // Оставляем только базовую очистку, так как ожидаем хороший Markdown с сервера
    return text.trim();
}

// Преобразование Markdown в HTML
function convertMarkdownToHtml(text) {
    if (!text) return '';

    // Глобальные замены для жирного, курсива и кода
    let html = text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>');

    const blocks = html.split('\n');
    let newHtml = '';
    let listTag = null;

    blocks.forEach(line => {
        const trimmedLine = line.trim();
        
        // Пропускаем пустые строки между блоками
        if (trimmedLine === '') {
            if (listTag) {
                newHtml += `</${listTag}>`;
                listTag = null;
            }
            return;
        }

        // Заголовки
        if (trimmedLine.startsWith('### ')) {
            newHtml += `<h3>${trimmedLine.substring(4)}</h3>`;
            listTag = null;
        } else if (trimmedLine.startsWith('## ')) {
            newHtml += `<h2>${trimmedLine.substring(3)}</h2>`;
            listTag = null;
        } else if (trimmedLine.startsWith('# ')) {
            newHtml += `<h1>${trimmedLine.substring(2)}</h1>`;
            listTag = null;
        } 
        // Элементы нумерованного списка
        else if (/^\d+\.\s/.test(trimmedLine)) {
            if (listTag !== 'ol') {
                if (listTag) newHtml += `</${listTag}>`;
                newHtml += '<ol>';
                listTag = 'ol';
            }
            newHtml += `<li>${trimmedLine.replace(/^\d+\.\s/, '')}</li>`;
        } 
        // Элементы маркированного списка
        else if (/^[-*•]\s/.test(trimmedLine)) {
            if (listTag !== 'ul') {
                if (listTag) newHtml += `</${listTag}>`;
                newHtml += '<ul>';
                listTag = 'ul';
            }
            newHtml += `<li>${trimmedLine.replace(/^[-*•]\s/, '')}</li>`;
        }
        // Обычный параграф
        else {
            if (listTag) {
                newHtml += `</${listTag}>`;
                listTag = null;
            }
            newHtml += `<p>${trimmedLine}</p>`;
        }
    });

    // Закрываем последний открытый список, если он есть
    if (listTag) {
        newHtml += `</${listTag}>`;
    }

    return newHtml;
}

// Отображение ответа
async function displayAnswer(userQuestion, botAnswer) {
    const answerContainer = document.getElementById('answer-container');
    const answerContent = document.getElementById('answer-content');
    if (!answerContainer || !answerContent) return;
    
    // Сохраняем данные для генерации связанных вопросов
    SuggestedQuestionsState.userQuestion = userQuestion;
    SuggestedQuestionsState.botAnswer = botAnswer;
    
    // Форматируем и конвертируем ответ
    const formattedAnswer = formatAnswerText(botAnswer);
    const htmlAnswer = convertMarkdownToHtml(formattedAnswer);
    
    const answerCard = createCard(`
        <h3 style="color: var(--tg-theme-text-color); margin-bottom: 12px;">Ответ:</h3>
        <div class="answer-text" style="color: var(--tg-theme-text-color);">${htmlAnswer}</div>
    `);
    
    answerContent.innerHTML = '';
    answerContent.appendChild(answerCard);
    answerContainer.classList.remove('hidden');
    
    // Прокрутка к самому верху страницы сразу после вывода ответа
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Запускаем асинхронную генерацию связанных вопросов
    await generateSuggestedQuestions();
    
    // Показываем предыдущие вопросы из истории в самом конце
    setTimeout(async () => {
        await displayPreviousQuestions();
    }, 100);
}

// Отображение предложенных вопросов
function displaySuggestedQuestions(questions) {
    const suggestedContainer = document.getElementById('suggested-questions');
    const suggestedList = document.getElementById('suggested-list');
    
    if (!suggestedContainer || !suggestedList) return;
    
    suggestedList.innerHTML = '';
    
    // Ограничиваем количество вопросов до 3
    const limitedQuestions = questions.slice(0, 3);
    
    limitedQuestions.forEach((question, index) => {
        const questionCard = document.createElement('div');
        questionCard.className = 'suggested-question-card';
        questionCard.style.cssText = `
            background: var(--tg-theme-secondary-bg-color);
            border: 1px solid var(--tg-theme-section-separator-color);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            position: relative;
            overflow: hidden;
        `;
        
        questionCard.innerHTML = `
            <div style="display: flex; align-items: flex-start; gap: 12px;">
                <div style="
                    background: var(--tg-theme-button-color);
                    color: var(--tg-theme-button-text-color);
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 12px;
                    font-weight: 600;
                    flex-shrink: 0;
                    margin-top: 2px;
                ">💡</div>
                <div style="
                    color: var(--tg-theme-text-color);
                    font-size: 15px;
                    line-height: 1.4;
                    flex: 1;
                ">${question}</div>
            </div>
        `;
        
        // Добавляем эффекты при взаимодействии
        questionCard.addEventListener('mousedown', () => {
            questionCard.style.transform = 'scale(0.98)';
            questionCard.style.backgroundColor = 'var(--tg-theme-section-bg-color)';
        });
        
        questionCard.addEventListener('mouseup', () => {
            questionCard.style.transform = 'scale(1)';
            questionCard.style.backgroundColor = 'var(--tg-theme-secondary-bg-color)';
        });
        
        questionCard.addEventListener('mouseleave', () => {
            questionCard.style.transform = 'scale(1)';
            questionCard.style.backgroundColor = 'var(--tg-theme-secondary-bg-color)';
        });
        
        questionCard.onclick = () => {
            document.getElementById('question-input').value = question;
            sendQuestion();
        };
        
        suggestedList.appendChild(questionCard);
    });
    
    suggestedContainer.classList.remove('hidden');
}

// Загрузка вопросов
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

// Загрузка ролей и специализаций
async function loadRolesAndSpecializations() {
    try {
        console.log('Загружаем роли и специализации с API:', CONFIG.API_BASE_URL);
        const [rolesResponse, specsResponse] = await Promise.all([
            fetch(`${CONFIG.API_BASE_URL}/roles`),
            fetch(`${CONFIG.API_BASE_URL}/specializations`)
        ]);
        
        console.log('Ответы API:', rolesResponse.status, specsResponse.status);
        
        if (rolesResponse.ok && specsResponse.ok) {
            roles = await rolesResponse.json();
            specializations = await specsResponse.json();
            console.log('Роли загружены:', roles);
            console.log('Специализации загружены:', specializations);
        } else {
            throw new Error('Ошибка загрузки данных');
        }
    } catch (error) {
        console.error('Ошибка загрузки ролей и специализаций:', error);
        console.log('Используем fallback данные');
        
        // Fallback данные, если API недоступен
        roles = [
            { "value": "PO/PM", "label": "PO/PM" },
            { "value": "Лид компетенции", "label": "Лид компетенции" },
            { "value": "Специалист", "label": "Специалист" },
            { "value": "Стажер", "label": "Стажер" }
        ];
        
        specializations = [
            { "value": "Аналитик", "label": "Аналитик" },
            { "value": "Тестировщик", "label": "Тестировщик" },
            { "value": "WEB", "label": "WEB" },
            { "value": "Java", "label": "Java" },
            { "value": "Python", "label": "Python" }
        ];
        
        console.log('Fallback роли:', roles);
        console.log('Fallback специализации:', specializations);
    }
}

async function loadQuestions() {
    try {
        // Получаем роль и специализацию пользователя
        const role = AppState.profile.role || '';
        const specialization = AppState.profile.specialization || '';
        
        // Формируем URL с параметрами роли и специализации
        const params = new URLSearchParams();
        if (role) params.append('role', role);
        if (specialization) params.append('specialization', specialization);
        
        const url = `${CONFIG.API_BASE_URL}/questions${params.toString() ? '?' + params.toString() : ''}`;
        console.log('Загружаем вопросы для роли:', role, 'специализации:', specialization, 'URL:', url);
        
        const response = await fetch(url);
        if (response.ok) {
            AppState.questions = await response.json();
            console.log('Загружено вопросов:', AppState.questions.length);
        } else {
            throw new Error('Ошибка загрузки вопросов');
        }
    } catch (error) {
        console.error('Ошибка загрузки вопросов:', error);
        // При ошибке загрузки показываем пустой массив
        AppState.questions = [];
    }
}

// Загрузка истории
async function loadHistory() {
    try {
        const userId = AppState.user?.id || 'guest';
        const response = await fetch(`${CONFIG.API_BASE_URL}/history/${userId}`);
        
        if (response.ok) {
            AppState.history = await response.json();
        } else {
            throw new Error('Ошибка загрузки истории');
        }
    } catch (error) {
        console.error('Ошибка загрузки истории:', error);
        AppState.history = [];
    }
}

// Показать уведомление
// Состояние для связанных вопросов
const SuggestedQuestionsState = {
    currentQuestions: [],
    userQuestion: '',
    botAnswer: ''
};

// Генерация связанных вопросов
async function generateSuggestedQuestions() {
    const suggestedContainer = document.getElementById('suggested-questions');
    const suggestedList = document.getElementById('suggested-list');
    
    if (!suggestedContainer || !suggestedList) return;
    
    try {
        // Показываем спиннер
        suggestedList.innerHTML = '<div class="spinner" style="margin: 20px auto;"></div>';
        suggestedContainer.classList.remove('hidden');
        
        // Пробуем WebSocket
        const ws = new WebSocket(CONFIG.WEBSOCKET_URL);
        let wsTimeout = setTimeout(() => {
            ws.close();
            generateSuggestedQuestionsHTTP();
        }, 5000);
        
        ws.onopen = () => {
            clearTimeout(wsTimeout);
            ws.send(JSON.stringify({
                type: 'generate_questions',
                user_question: SuggestedQuestionsState.userQuestion,
                bot_answer: SuggestedQuestionsState.botAnswer,
                role: AppState.profile.role,
                specialization: AppState.profile.specialization
            }));
        };
        
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'suggested_questions') {
                const questions = Array.isArray(data.questions) ? data.questions : data.questions || [];
                SuggestedQuestionsState.currentQuestions = questions;
                displaySuggestedQuestions(questions);
                ws.close();
            }
        };
        
        ws.onerror = () => {
            clearTimeout(wsTimeout);
            generateSuggestedQuestionsHTTP();
        };
        
    } catch (error) {
        console.error('Ошибка WebSocket:', error);
        generateSuggestedQuestionsHTTP();
    }
}

// HTTP fallback для связанных вопросов
async function generateSuggestedQuestionsHTTP() {
    try {
        const response = await fetch(`${CONFIG.API_BASE_URL}/suggest_questions`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_question: SuggestedQuestionsState.userQuestion,
                bot_answer: SuggestedQuestionsState.botAnswer,
                role: AppState.profile.role,
                specialization: AppState.profile.specialization
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('HTTP ответ для связанных вопросов:', data);
            // API возвращает массив вопросов напрямую
            const questions = Array.isArray(data) ? data : data.questions || [];
            console.log('Обработанные связанные вопросы:', questions);
            SuggestedQuestionsState.currentQuestions = questions;
            displaySuggestedQuestions(questions);
        }
    } catch (error) {
        console.error('Ошибка HTTP генерации вопросов:', error);
        const suggestedContainer = document.getElementById('suggested-questions');
        if (suggestedContainer) {
            suggestedContainer.classList.add('hidden');
        }
    }
}

// Отображение предыдущих вопросов
async function displayPreviousQuestions() {
    console.log('📜 displayPreviousQuestions вызвана');
    
    const previousContainer = document.getElementById('previous-questions');
    const previousList = document.getElementById('previous-list');
    
    if (!previousContainer || !previousList) {
        console.log('❌ Элементы previous-questions не найдены');
        return;
    }
    
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
        const recentQuestions = historyFromDB.slice(1, 4); // Пропускаем первый (текущий) вопрос
        
        console.log('📍 Предыдущие вопросы из БД:', recentQuestions);
        console.log('📍 Количество предыдущих вопросов:', recentQuestions.length);
        
        if (!recentQuestions || recentQuestions.length === 0) {
            console.log('⚠️ Нет предыдущих вопросов для отображения');
            previousContainer.classList.add('hidden');
            return;
        }
        
        console.log('🔄 Создаем кнопки предыдущих вопросов...');
        previousList.innerHTML = '';
    
        recentQuestions.forEach((historyItem, index) => {
            console.log(`➕ Добавляем предыдущий вопрос ${index + 1}:`, historyItem.question.substring(0, 50));
            
            const historyCard = document.createElement('div');
            historyCard.className = 'previous-question-card';
            historyCard.style.cssText = `
                background: var(--tg-theme-secondary-bg-color);
                border: 1px solid var(--tg-theme-section-separator-color);
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 8px;
                cursor: pointer;
                transition: all 0.2s ease;
                position: relative;
                overflow: hidden;
            `;
            
            const questionText = historyItem.question.length > 100 ? 
                historyItem.question.substring(0, 100) + '...' : 
                historyItem.question;
            
            historyCard.innerHTML = `
                <div style="display: flex; align-items: flex-start; gap: 12px;">
                    <div style="
                        background: var(--tg-theme-hint-color);
                        color: var(--tg-theme-bg-color);
                        width: 24px;
                        height: 24px;
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 12px;
                        font-weight: 600;
                        flex-shrink: 0;
                        margin-top: 2px;
                        opacity: 0.8;
                    ">📜</div>
                    <div style="
                        color: var(--tg-theme-text-color);
                        font-size: 15px;
                        line-height: 1.4;
                        flex: 1;
                    ">${questionText}</div>
                </div>
            `;
            
            // Добавляем эффекты при взаимодействии
            historyCard.addEventListener('mousedown', () => {
                historyCard.style.transform = 'scale(0.98)';
                historyCard.style.backgroundColor = 'var(--tg-theme-section-bg-color)';
            });
            
            historyCard.addEventListener('mouseup', () => {
                historyCard.style.transform = 'scale(1)';
                historyCard.style.backgroundColor = 'var(--tg-theme-secondary-bg-color)';
            });
            
            historyCard.addEventListener('mouseleave', () => {
                historyCard.style.transform = 'scale(1)';
                historyCard.style.backgroundColor = 'var(--tg-theme-secondary-bg-color)';
            });
            
            historyCard.onclick = () => {
                console.log('🔄 Пользователь выбрал предыдущий вопрос:', historyItem.question);
                showHistoryDetail(historyItem);
            };
            
            previousList.appendChild(historyCard);
        });
        
        previousContainer.classList.remove('hidden');
        console.log('✅ Предыдущие вопросы отображены');
        
    } catch (error) {
        console.error('❌ Ошибка загрузки предыдущих вопросов:', error);
        previousContainer.classList.add('hidden');
    }
}

function showAlert(message) {
    if (tg && tg.showAlert) {
        tg.showAlert(message);
    } else {
        alert(message);
    }
}

// Лоадеры
function showLoader() {
    let loader = document.getElementById('global-loader');
    if (!loader) {
        loader = document.createElement('div');
        loader.id = 'global-loader';
        loader.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        `;
        loader.innerHTML = '<div class="spinner" style="width: 40px; height: 40px;"></div>';
        document.body.appendChild(loader);
    }
    loader.style.display = 'flex';
}

function hideLoader() {
    const loader = document.getElementById('global-loader');
    if (loader) {
        loader.style.display = 'none';
    }
}

// Настройка обработчиков событий
function setupEventListeners() {
    // Обработка изменения темы
    if (tg) {
        // Слушаем изменения темы Telegram
        document.addEventListener('themeChanged', () => {
            console.log('Тема изменена');
        });
    }
}

// Загрузка начальных данных
async function loadInitialData() {
    try {
        // Здесь можно загрузить начальные данные
        console.log('Загрузка начальных данных...');
    } catch (error) {
        console.error('Ошибка загрузки начальных данных:', error);
    }
}

// Получить иконку роли
function getRoleIcon(role) {
    const icons = {
        'junior': '🌱',
        'middle': '🚀',
        'senior': '👑',
        'lead': '⭐',
        'architect': '🏗️',
        'manager': '📊',
        'analyst': '📈',
        'designer': '🎨',
        'qa': '🔍',
        'devops': '⚙️',
        'data': '📊',
        'mobile': '📱',
        'frontend': '🎨',
        'backend': '⚡',
        'fullstack': '🌐'
    };
    
    return icons[role] || '👤';
}

// Показать скелетон загрузки вопросов
function showQuestionsLoadingSkeleton(container) {
    const skeleton = `
        <div class="skeleton-item" style="margin-bottom: 16px;">
            <div class="skeleton-line" style="width: 100%; height: 20px; background: var(--tg-theme-section-separator-color); border-radius: 4px; margin-bottom: 8px;"></div>
            <div class="skeleton-line" style="width: 80%; height: 16px; background: var(--tg-theme-section-separator-color); border-radius: 4px; margin-bottom: 8px;"></div>
            <div class="skeleton-line" style="width: 60%; height: 14px; background: var(--tg-theme-section-separator-color); border-radius: 4px;"></div>
        </div>
        <div class="skeleton-item" style="margin-bottom: 16px;">
            <div class="skeleton-line" style="width: 100%; height: 20px; background: var(--tg-theme-section-separator-color); border-radius: 4px; margin-bottom: 8px;"></div>
            <div class="skeleton-line" style="width: 70%; height: 16px; background: var(--tg-theme-section-separator-color); border-radius: 4px; margin-bottom: 8px;"></div>
            <div class="skeleton-line" style="width: 50%; height: 14px; background: var(--tg-theme-section-separator-color); border-radius: 4px;"></div>
        </div>
        <div class="skeleton-item" style="margin-bottom: 16px;">
            <div class="skeleton-line" style="width: 100%; height: 20px; background: var(--tg-theme-section-separator-color); border-radius: 4px; margin-bottom: 8px;"></div>
            <div class="skeleton-line" style="width: 90%; height: 16px; background: var(--tg-theme-section-separator-color); border-radius: 4px; margin-bottom: 8px;"></div>
            <div class="skeleton-line" style="width: 40%; height: 14px; background: var(--tg-theme-section-separator-color); border-radius: 4px;"></div>
        </div>
    `;
    
    container.innerHTML = skeleton;
}

// Показать скелетон загрузки истории
function showHistoryLoadingSkeleton(container) {
    const skeleton = `
        <div class="skeleton-item" style="margin-bottom: 16px; padding: 16px; border: 1px solid var(--tg-theme-section-separator-color); border-radius: 8px;">
            <div class="skeleton-line" style="width: 100%; height: 18px; background: var(--tg-theme-section-separator-color); border-radius: 4px; margin-bottom: 8px;"></div>
            <div class="skeleton-line" style="width: 80%; height: 14px; background: var(--tg-theme-section-separator-color); border-radius: 4px; margin-bottom: 8px;"></div>
            <div class="skeleton-line" style="width: 30%; height: 12px; background: var(--tg-theme-section-separator-color); border-radius: 4px;"></div>
        </div>
        <div class="skeleton-item" style="margin-bottom: 16px; padding: 16px; border: 1px solid var(--tg-theme-section-separator-color); border-radius: 8px;">
            <div class="skeleton-line" style="width: 100%; height: 18px; background: var(--tg-theme-section-separator-color); border-radius: 4px; margin-bottom: 8px;"></div>
            <div class="skeleton-line" style="width: 70%; height: 14px; background: var(--tg-theme-section-separator-color); border-radius: 4px; margin-bottom: 8px;"></div>
            <div class="skeleton-line" style="width: 25%; height: 12px; background: var(--tg-theme-section-separator-color); border-radius: 4px;"></div>
        </div>
        <div class="skeleton-item" style="margin-bottom: 16px; padding: 16px; border: 1px solid var(--tg-theme-section-separator-color); border-radius: 8px;">
            <div class="skeleton-line" style="width: 100%; height: 18px; background: var(--tg-theme-section-separator-color); border-radius: 4px; margin-bottom: 8px;"></div>
            <div class="skeleton-line" style="width: 90%; height: 14px; background: var(--tg-theme-section-separator-color); border-radius: 4px; margin-bottom: 8px;"></div>
            <div class="skeleton-line" style="width: 35%; height: 12px; background: var(--tg-theme-section-separator-color); border-radius: 4px;"></div>
        </div>
    `;
    
    container.innerHTML = skeleton;
}

// Показать кастомное модальное окно подтверждения
function showConfirmationModal(title, text, onConfirm) {
    let modal = document.getElementById('confirmation-modal');
    if (modal) {
        modal.remove();
    }
    
    modal = document.createElement('div');
    modal.id = 'confirmation-modal';
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10001;
        padding: 20px;
    `;

    function closeModal() {
        modal.style.opacity = '0';
        setTimeout(() => modal.remove(), 200);
    }

    modal.innerHTML = `
        <div class="modal-content" style="
            background: var(--tg-theme-secondary-bg-color);
            border-radius: 14px;
            max-width: 320px;
            width: 100%;
            text-align: center;
            padding-top: 24px;
        ">
            <h3 style="margin: 0 16px 8px; font-size: 17px; font-weight: 600; color: var(--tg-theme-text-color);">${title}</h3>
            <p style="margin: 0 16px 20px; font-size: 14px; color: var(--tg-theme-text-color); line-height: 1.4;">${text}</p>
            <div class="modal-actions" style="border-top: 1px solid var(--tg-theme-section-separator-color); display: flex;">
                <button id="confirm-cancel" style="width: 50%; padding: 14px; border: 0; background: none; font-size: 17px; color: var(--tg-theme-link-color); border-right: 1px solid var(--tg-theme-section-separator-color);">Отмена</button>
                <button id="confirm-ok" style="width: 50%; padding: 14px; border: 0; background: none; font-size: 17px; color: var(--tg-theme-destructive-text-color); font-weight: 600;">Очистить</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    document.getElementById('confirm-ok').onclick = () => {
        closeModal();
        onConfirm();
    };
    
    document.getElementById('confirm-cancel').onclick = closeModal;
} 