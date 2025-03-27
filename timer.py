import streamlit as st
import time
from datetime import datetime, timedelta

def start_game():
    """
    Start a new game
    """
    st.session_state.game_active = True
    st.session_state.game_paused = False
    st.session_state.start_time = datetime.now()
    st.session_state.elapsed_pause_time = 0
    
    # Обновляем время последнего обновления и включаем принудительное обновление
    if 'last_update_time' in st.session_state:
        st.session_state.last_update_time = time.time()
    if 'force_refresh' in st.session_state:
        st.session_state.force_refresh = True

def pause_game():
    """
    Pause the current game
    """
    if st.session_state.game_active and not st.session_state.game_paused:
        st.session_state.game_paused = True
        st.session_state.pause_time = datetime.now()
        
        # Включаем принудительное обновление для обновления интерфейса
        if 'force_refresh' in st.session_state:
            st.session_state.force_refresh = True

def resume_game():
    """
    Resume a paused game
    """
    if st.session_state.game_active and st.session_state.game_paused:
        # Calculate how long the game was paused
        pause_duration = (datetime.now() - st.session_state.pause_time).total_seconds()
        st.session_state.elapsed_pause_time += pause_duration
        st.session_state.game_paused = False
        
        # Обновляем время последнего обновления и включаем принудительное обновление
        if 'last_update_time' in st.session_state:
            st.session_state.last_update_time = time.time()
        if 'force_refresh' in st.session_state:
            st.session_state.force_refresh = True

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
    
    # Принудительно включаем обновление
    st.session_state.force_refresh = True
    
    # Сбрасываем также время последнего обновления
    st.session_state.last_update_time = time.time()

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
