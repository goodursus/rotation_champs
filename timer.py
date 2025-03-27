import streamlit as st
import time
from datetime import datetime, timedelta

def start_game():
    """
    Start a new game
    """
    # Сначала сбрасываем все значения
    st.session_state.game_active = True
    st.session_state.game_paused = False
    st.session_state.start_time = datetime.now()
    st.session_state.elapsed_pause_time = 0
    
    # Увеличиваем счетчик запусков для отслеживания изменений
    if 'start_counter' not in st.session_state:
        st.session_state.start_counter = 0
    st.session_state.start_counter += 1
    
    # Обновляем время последнего обновления для автообновления
    st.session_state.last_update_time = time.time()
    
    # Принудительно включаем обновление
    st.session_state.force_refresh = True
    
    # Выводим диагностическое сообщение
    print(f"Игра запущена: {time.time()}, active={st.session_state.game_active}, start_time={st.session_state.start_time}")

def pause_game():
    """
    Pause the current game
    """
    # Проверяем, активна ли игра и не приостановлена ли она
    if st.session_state.game_active and not st.session_state.game_paused:
        # Устанавливаем флаг паузы и запоминаем время
        st.session_state.game_paused = True
        st.session_state.pause_time = datetime.now()
        
        # Принудительно обновляем интерфейс
        st.session_state.force_refresh = True
        
        # Выводим логи для отладки
        print(f"Игра приостановлена: {datetime.now()}, игра активна={st.session_state.game_active}, пауза={st.session_state.game_paused}")

def resume_game():
    """
    Resume a paused game
    """
    # Проверяем, что игра активна и приостановлена
    if st.session_state.game_active and st.session_state.game_paused:
        # Безопасная проверка, что время паузы существует
        if st.session_state.pause_time is None:
            st.session_state.pause_time = datetime.now()
            
        # Рассчитываем, как долго была пауза
        pause_duration = (datetime.now() - st.session_state.pause_time).total_seconds()
        
        # Обновляем общее время на паузе и снимаем флаг паузы
        st.session_state.elapsed_pause_time += pause_duration
        st.session_state.game_paused = False
        
        # Обновляем время последнего обновления для автообновления
        st.session_state.last_update_time = time.time()
        
        # Принудительно обновляем интерфейс
        st.session_state.force_refresh = True
        
        # Выводим логи для отладки
        print(f"Игра возобновлена: {datetime.now()}, пауза длилась {pause_duration:.2f} секунд, общее время пауз: {st.session_state.elapsed_pause_time:.2f}")

def reset_game():
    """
    Reset the game timer
    """
    # Полностью сбрасываем все переменные состояния игры
    st.session_state.game_active = False
    st.session_state.game_paused = False
    st.session_state.start_time = None
    st.session_state.pause_time = None
    st.session_state.elapsed_pause_time = 0
    
    # Увеличиваем счетчик сбросов для отслеживания изменений в таймере
    if 'reset_counter' not in st.session_state:
        st.session_state.reset_counter = 0
    st.session_state.reset_counter += 1
    
    # Принудительно включаем обновление и обновляем время
    st.session_state.force_refresh = True
    st.session_state.last_update_time = time.time()
    
    # Выводим диагностическое сообщение для отладки
    print(f"Таймер сброшен: {time.time()}")

def calculate_game_time():
    """
    Calculate elapsed and remaining game time with seconds precision
    
    Returns:
    - elapsed_minutes: Minutes elapsed since game started
    - elapsed_seconds: Seconds part of elapsed time
    - remaining_minutes: Minutes remaining in the game
    - remaining_seconds: Seconds part of remaining time
    """
    if not st.session_state.game_active or st.session_state.start_time is None:
        return 0, 0, st.session_state.game_duration, 0
    
    # Безопасная обработка случая, когда игра активна, но время паузы не определено
    if st.session_state.game_paused:
        if st.session_state.pause_time is None:
            st.session_state.pause_time = datetime.now()
            
        # If game is paused, calculate elapsed time up to when it was paused
        elapsed_seconds_total = (st.session_state.pause_time - st.session_state.start_time).total_seconds() - st.session_state.elapsed_pause_time
    else:
        # Calculate elapsed time considering any pauses
        elapsed_seconds_total = (datetime.now() - st.session_state.start_time).total_seconds() - st.session_state.elapsed_pause_time
    
    # Убедимся, что elapsed_seconds_total не отрицательное
    elapsed_seconds_total = max(0, elapsed_seconds_total)
    
    # Calculate elapsed minutes and seconds
    elapsed_minutes = int(elapsed_seconds_total // 60)
    elapsed_seconds = int(elapsed_seconds_total % 60)
    
    # Calculate total game duration in seconds
    total_duration_seconds = st.session_state.game_duration * 60
    
    # Calculate remaining seconds
    remaining_seconds_total = max(0, total_duration_seconds - elapsed_seconds_total)
    
    # Calculate remaining minutes and seconds
    remaining_minutes = int(remaining_seconds_total // 60)
    remaining_seconds = int(remaining_seconds_total % 60)
    
    return elapsed_minutes, elapsed_seconds, remaining_minutes, remaining_seconds
