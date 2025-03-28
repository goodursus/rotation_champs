import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import random
import html

def display_leaderboard():
    """
    Отображает динамическую таблицу лидеров с анимацией изменения позиций
    и цветовой кодировкой игроков
    """
    st.markdown("""
    <style>
    .leaderboard-container {
        padding: 15px;
        border-radius: 10px;
        background-color: #f5f5f5;
    }
    .leaderboard-header {
        font-weight: bold;
        background-color: #4CAF50;
        color: white;
        padding: 8px;
        border-radius: 5px 5px 0 0;
    }
    .leaderboard-row {
        padding: 8px;
        border-bottom: 1px solid #e0e0e0;
        transition: background-color 0.3s;
    }
    .leaderboard-row:hover {
        background-color: #e0f7fa;
    }
    .position-up {
        color: #4CAF50;
    }
    .position-down {
        color: #F44336;
    }
    .position-same {
        color: #9E9E9E;
    }
    .rating-high {
        color: #4CAF50;
        font-weight: bold;
    }
    .rating-medium {
        color: #FFC107;
        font-weight: bold;
    }
    .rating-low {
        color: #F44336;
        font-weight: bold;
    }
    .win-rate-high {
        background-color: rgba(76, 175, 80, 0.2);
        padding: 3px 6px;
        border-radius: 10px;
    }
    .win-rate-medium {
        background-color: rgba(255, 193, 7, 0.2);
        padding: 3px 6px;
        border-radius: 10px;
    }
    .win-rate-low {
        background-color: rgba(244, 67, 54, 0.2);
        padding: 3px 6px;
        border-radius: 10px;
    }
    .player-name {
        font-weight: bold;
    }
    /* Анимация изменения позиции */
    @keyframes slide-up {
        0% { transform: translateY(10px); opacity: 0.5; }
        100% { transform: translateY(0); opacity: 1; }
    }
    @keyframes slide-down {
        0% { transform: translateY(-10px); opacity: 0.5; }
        100% { transform: translateY(0); opacity: 1; }
    }
    @keyframes highlight {
        0% { background-color: rgba(76, 175, 80, 0.2); }
        50% { background-color: rgba(76, 175, 80, 0.4); }
        100% { background-color: rgba(76, 175, 80, 0.2); }
    }
    .position-changed-up {
        animation: slide-up 0.5s ease, highlight 1s ease;
    }
    .position-changed-down {
        animation: slide-down 0.5s ease, highlight 1s ease;
    }
    .leaderboard-timestamp {
        font-size: 0.8em;
        color: #757575;
        font-style: italic;
        text-align: right;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Получаем текущую дату и время
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    
    # Функция для форматирования изменения позиции
    def format_position_change(change):
        """Форматирует изменение позиции с соответствующими стрелками и цветом"""
        if change > 0:
            return f'<span class="position-up">▲{change}</span>'
        elif change < 0:
            return f'<span class="position-down">▼{abs(change)}</span>'
        else:
            return f'<span class="position-same">-</span>'
    
    # Функция для определения цвета рейтинга
    def get_rating_color(rating):
        """Возвращает цвет для рейтинга"""
        if rating >= 100:
            return "rating-high"
        elif rating >= 50:
            return "rating-medium"
        else:
            return "rating-low"
    
    # Функция для форматирования рейтинга с цветом
    def format_rating_html(row):
        rating_class = get_rating_color(row['rating'])
        return f'<span class="{rating_class}">{row["rating"]}</span>'
    
    # Функция для форматирования процента побед с цветом
    def format_win_rate_html(row):
        win_rate = row['win_rate']
        if win_rate >= 0.7:
            return f'<span class="win-rate-high">{win_rate:.0%}</span>'
        elif win_rate >= 0.4:
            return f'<span class="win-rate-medium">{win_rate:.0%}</span>'
        else:
            return f'<span class="win-rate-low">{win_rate:.0%}</span>'
    
    # Если нет сохраненных предыдущих позиций игроков, создаем их
    if 'previous_rankings' not in st.session_state:
        st.session_state.previous_rankings = {}
    
    # Сортируем игроков по рейтингу
    df = st.session_state.players_df.copy()
    
    # Добавляем % побед
    df['total_games'] = df['wins'] + df['losses']
    df['win_rate'] = df.apply(
        lambda row: row['wins'] / row['total_games'] if row['total_games'] > 0 else 0, 
        axis=1
    )
    
    # Сортируем по рейтингу (убывание)
    df = df.sort_values(by='rating', ascending=False).reset_index(drop=True)
    
    # Добавляем текущую позицию
    df['position'] = df.index + 1
    
    # Вычисляем изменение позиции по сравнению с предыдущим состоянием
    df['position_change'] = df.apply(
        lambda row: st.session_state.previous_rankings.get(row['name'], row['position']) - row['position'], 
        axis=1
    )
    
    # Определяем класс для анимации изменения позиции
    df['position_animation'] = df.apply(
        lambda row: 'position-changed-up' if row['position_change'] > 0 else 
                    'position-changed-down' if row['position_change'] < 0 else '',
        axis=1
    )
    
    # Сохраняем текущие позиции для следующего обновления
    st.session_state.previous_rankings = dict(zip(df['name'], df['position']))
    
    # Создаем HTML-таблицу с динамическими классами для анимации
    html_table = '<div class="leaderboard-container">'
    html_table += '<div class="leaderboard-header">Таблица Лидеров</div>'
    
    # Цикл по игрокам для создания строк таблицы
    for _, row in df.iterrows():
        position_change_html = format_position_change(row['position_change'])
        rating_html = format_rating_html(row)
        win_rate_html = format_win_rate_html(row)
        
        # Создаем строку таблицы с классом для анимации
        html_table += f"""
        <div class="leaderboard-row {row['position_animation']}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.2em; font-weight: bold; min-width: 30px;">#{row['position']}</span>
                    <span class="player-name">{html.escape(row['name'])}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <span>{position_change_html}</span>
                    <span style="min-width: 60px;">W: {row['wins']} L: {row['losses']}</span>
                    <span style="min-width: 50px;">{win_rate_html}</span>
                    <span style="min-width: 50px;">{rating_html}</span>
                </div>
            </div>
        </div>
        """
    
    # Добавляем временную метку
    html_table += f'<div class="leaderboard-timestamp">Обновлено: {current_time}</div>'
    html_table += '</div>'
    
    # Отображаем таблицу
    st.markdown(html_table, unsafe_allow_html=True)
    
    # Добавляем опцию для автообновления таблицы лидеров
    st.checkbox(
        "Автоматическое обновление таблицы лидеров", 
        value=st.session_state.get('auto_refresh_leaderboard', False),
        key='auto_refresh_leaderboard'
    )
    
    # Автоматическое обновление, если включено
    if st.session_state.get('auto_refresh_leaderboard', False):
        time.sleep(5)  # Обновляем каждые 5 секунд
        st.rerun()


def display_leaderboard_animation_demo():
    """
    Демонстрирует анимацию таблицы лидеров, симулируя изменения рейтинга
    """
    st.markdown("### Демо анимации таблицы лидеров")
    st.markdown("""
    Эта демонстрация показывает, как работает анимация изменения позиций в таблице лидеров.
    Нажмите кнопку ниже, чтобы симулировать изменение рейтингов игроков и увидеть анимацию.
    """)
    
    # Кнопка для запуска симуляции
    if st.button("Симулировать изменения рейтингов"):
        # Создаем копию текущих данных игроков
        df = st.session_state.players_df.copy()
        
        # Применяем случайные изменения рейтинга
        for i, row in df.iterrows():
            # Случайное изменение рейтинга от -20 до +30
            rating_change = random.randint(-20, 30)
            df.at[i, 'rating'] = max(0, row['rating'] + rating_change)
            
            # Если рейтинг увеличился, то добавляем победу, иначе поражение
            if rating_change > 0:
                df.at[i, 'wins'] += 1
            elif rating_change < 0:
                df.at[i, 'losses'] += 1
        
        # Обновляем данные игроков
        st.session_state.players_df = df
        
        # Показываем уведомление
        st.success("Рейтинги игроков обновлены! Посмотрите анимацию в таблице лидеров.")
        
        # Перезагружаем страницу для отображения изменений
        time.sleep(0.5)  # Небольшая задержка для лучшего UX
        st.rerun()