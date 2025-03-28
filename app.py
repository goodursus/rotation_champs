import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import player_management as pm
import court_allocation as ca
import timer as tm
import tournament as tr
import player_matching as match
import court_designer as designer
import leaderboard as lb

# Set page configuration
st.set_page_config(
    page_title="Rotation Players",
    page_icon="🏸",
    layout="wide"
)

# Используем новую функцию автообновления Streamlit
def enable_auto_refresh():
    """
    Включает автоматическое обновление страницы с таймером
    """
    # Если игра активна и не на паузе, включаем автообновление каждую секунду
    if st.session_state.get('game_active', False) and not st.session_state.get('game_paused', True):
        time.sleep(0.1)  # Небольшая задержка для снижения нагрузки
        st.rerun()

# Инициализируем счетчик обновлений для отображения изменений в таймере
if 'update_counter' not in st.session_state:
    st.session_state.update_counter = 0
else:
    # Увеличиваем счетчик при каждом обновлении, если игра активна и не на паузе
    if st.session_state.get('game_active', False) and not st.session_state.get('game_paused', True):
        st.session_state.update_counter += 1

# Initialize session state variables if they don't exist
if 'players_df' not in st.session_state:
    # Initialize with sample players for example (14 players)
    st.session_state.players_df = pd.DataFrame({
        'id': list(range(1, 15)),
        'name': [f"Player {i}" for i in range(1, 15)],
        'wins': [0] * 14,
        'losses': [0] * 14,
        'points_difference': [0] * 14,
        'rating': [0] * 14
    })

if 'courts' not in st.session_state:
    st.session_state.courts = []

if 'game_active' not in st.session_state:
    st.session_state.game_active = False

if 'game_paused' not in st.session_state:
    st.session_state.game_paused = False

if 'game_duration' not in st.session_state:
    st.session_state.game_duration = 15  # Default 15 minutes

if 'start_time' not in st.session_state:
    st.session_state.start_time = None

if 'pause_time' not in st.session_state:
    st.session_state.pause_time = None

if 'elapsed_pause_time' not in st.session_state:
    st.session_state.elapsed_pause_time = 0

# Инициализируем настройки для алгоритма подбора игроков
if 'matchmaking_strategy' not in st.session_state:
    st.session_state.matchmaking_strategy = 'Случайное распределение'

# Main application layout
st.title("Rotation Players")

# Create tabs for separating content
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Courts & Timer", "Player Statistics", "Tournament", "Leaderboard", "Court Designer"])

with tab1:
    # Create layout with two columns
    col1, col2 = st.columns([2, 1])

    with col1:
        # Display courts with players
        st.header("Courts")
        
        # Добавляем раздел настроек подбора игроков
        with st.expander("Настройки подбора игроков"):
            st.session_state.matchmaking_strategy = st.radio(
                "Выберите стратегию распределения игроков:",
                ["Случайное распределение", "Сбалансированные команды по навыкам"]
            )
            
            if st.session_state.matchmaking_strategy == "Сбалансированные команды по навыкам":
                st.info("""
                    **Описание алгоритма:** 
                    Этот алгоритм распределяет игроков на основе их рейтинга для создания 
                    максимально сбалансированных команд. Игроки с высоким рейтингом 
                    распределяются между кортами методом "змейки", чтобы обеспечить их 
                    равномерное распределение. Затем внутри каждого корта игроки делятся 
                    на команды так, чтобы минимизировать разницу в суммарном рейтинге команд.
                """)
            else:
                st.info("""
                    **Описание алгоритма:** 
                    Случайное распределение игроков по кортам без учета рейтинга.
                """)
        
        # Отображение кортов
        if st.session_state.courts:
            ca.display_courts(st.session_state.courts, st.session_state.players_df)
        else:
            st.info("Click 'Distribute Players' to allocate players to courts.")

        # Game timer controls
        st.header("Game Timer")
        
        # Добавляем статус таймера
        timer_status = ""
        if st.session_state.game_active:
            if st.session_state.game_paused:
                timer_status = "⏸️ Приостановлено"
            else:
                timer_status = "▶️ Активно"
        else:
            timer_status = "⏹️ Не запущено"
            
        st.write(f"**Статус таймера:** {timer_status}")
        
        col_timer1, col_timer2, col_timer3 = st.columns(3)
        
        with col_timer1:
            st.session_state.game_duration = st.number_input(
                "Game Duration (minutes)", 
                min_value=1, 
                max_value=120, 
                value=st.session_state.game_duration
            )
            
        with col_timer2:
            elapsed_time, elapsed_seconds, remaining_time, remaining_seconds = tm.calculate_game_time()
            
            # Показатели секундомера
            update_count = st.session_state.get('update_counter', 0)
            reset_count = st.session_state.get('reset_counter', 0)
            
            # Добавляем небольшую визуальную подсказку о состоянии таймера
            elapsed_label = "Elapsed Time"
            if st.session_state.game_active:
                if not st.session_state.game_paused:
                    elapsed_label = "⏱ Elapsed Time"
                    delta_value = "+1s" if update_count > 0 else None
                else:
                    elapsed_label = "⏸ Elapsed Time"
                    delta_value = None
            else:
                elapsed_label = "⏹ Elapsed Time"
                delta_value = None
                
            # Отображаем метрику с дополнительной информацией
            st.metric(
                elapsed_label, 
                f"{elapsed_time}:{elapsed_seconds:02d}", 
                delta=delta_value, 
                delta_color="normal" if delta_value else "off",
                help=f"Updates: {update_count}, Resets: {reset_count}"
            )
            
        with col_timer3:
            # Показываем оставшееся время
            remaining_label = "Remaining Time"
            if st.session_state.game_active and not st.session_state.game_paused:
                remaining_label = "⏱ Remaining Time"
                delta_value = "-1s" if update_count > 0 else None
            else:
                delta_value = None
                
            st.metric(
                remaining_label, 
                f"{remaining_time}:{remaining_seconds:02d}", 
                delta=delta_value, 
                delta_color="normal" if delta_value else "off",
                help=f"Duration: {st.session_state.game_duration} min"
            )
        
        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
        
        # Проверяем, активен ли турнир
        active_tournament_id = st.session_state.get('active_tournament_id')
        tournament_active = active_tournament_id is not None
        
        # Если турнир не активен, блокируем кнопки таймера с пояснением
        if not tournament_active:
            st.warning("Для активации таймера необходимо запустить турнир на вкладке 'Tournament'")
        
        with col_btn1:
            if not st.session_state.game_active:
                if st.button("Start Game", use_container_width=True, disabled=not tournament_active):
                    tm.start_game()
                    st.rerun()
            else:
                if st.session_state.game_paused:
                    if st.button("Resume Game", use_container_width=True, disabled=not tournament_active):
                        tm.resume_game()
                        st.rerun()
                else:
                    if st.button("Pause Game", use_container_width=True, disabled=not tournament_active):
                        tm.pause_game()
                        st.rerun()
        
        with col_btn2:
            if st.button("Reset Timer", use_container_width=True, disabled=not tournament_active):
                tm.reset_game()
                st.rerun()
        
        with col_btn3:
            if st.button("Distribute Players", use_container_width=True):
                st.session_state.courts = ca.distribute_players(st.session_state.players_df)
                st.rerun()
                
        with col_btn4:
            if st.button("Rotate Players", use_container_width=True):
                ca.rotate_players()
                st.rerun()

    with col2:
        # Player management section
        st.header("Players")
        pm.manage_players()

with tab2:
    # Display player statistics
    st.header("Player Statistics")
    pm.display_player_stats()

with tab3:
    # Отображаем турнирную сетку и функциональность турнира
    st.header("Tournament Mode")
    tr.display_tournament()

with tab4:
    # Отображаем динамическую таблицу лидеров
    st.header("Leaderboard")
    # Основная таблица лидеров
    lb.display_leaderboard()
    
    # Демо возможностей анимации
    with st.expander("Демо анимации таблицы лидеров"):
        lb.display_leaderboard_animation_demo()

with tab5:
    # Отображаем дизайнер кортов
    st.header("Court Designer")
    designer.display_court_designer()

# Проверяем, нужно ли сбросить таймер (например, после автогенерации результатов по таймеру)
if st.session_state.get('timer_needs_reset', False):
    # Сбрасываем флаг
    st.session_state.timer_needs_reset = False
    # Сбрасываем таймер
    tm.reset_game()
    # Делаем перезагрузку страницы
    st.rerun()

# Показываем уведомление о сгенерированных результатах, если оно есть
if st.session_state.get('show_results_notification', False):
    # Отображаем главное уведомление
    st.success("Время вышло! Автоматически сгенерированы результаты игр. Просмотрите и сохраните их.")
    # Сбрасываем уведомление при следующем обновлении страницы
    st.session_state.show_results_notification = False

# Включаем автообновление страницы, если таймер активен
enable_auto_refresh()
