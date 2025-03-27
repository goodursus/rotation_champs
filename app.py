import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import player_management as pm
import court_allocation as ca
import timer as tm

# Set page configuration
st.set_page_config(
    page_title="Rotation Players",
    page_icon="🏸",
    layout="wide"
)

# Добавим проверку для предотвращения бесконечного автообновления
# и переключатель для отслеживания принудительного обновления
if 'last_update_time' not in st.session_state:
    st.session_state.last_update_time = time.time()
    
if 'force_refresh' not in st.session_state:
    st.session_state.force_refresh = False

# Автоматическое обновление каждую секунду, только если игра активна и не на паузе
current_time = time.time()
if ('game_active' in st.session_state and 
    st.session_state.game_active and 
    not st.session_state.game_paused and
    (current_time - st.session_state.last_update_time >= 1.0 or st.session_state.force_refresh)):
    
    # Сбросить флаг принудительного обновления
    st.session_state.force_refresh = False
    # Обновить время последнего обновления
    st.session_state.last_update_time = current_time
    
    # Добавим небольшую задержку, чтобы предотвратить быстрое автообновление
    if not st.session_state.force_refresh:
        time.sleep(0.5)
        
    # Перезапустить приложение
    st.rerun()

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

# Main application layout
st.title("Rotation Players")

# Create tabs for separating content
tab1, tab2 = st.tabs(["Courts & Timer", "Player Statistics"])

with tab1:
    # Create layout with two columns
    col1, col2 = st.columns([2, 1])

    with col1:
        # Display courts with players
        st.header("Courts")
        if st.session_state.courts:
            ca.display_courts(st.session_state.courts, st.session_state.players_df)
        else:
            st.info("Click 'Distribute Players' to allocate players to courts.")

        # Game timer controls
        st.header("Game Timer")
        
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
            st.metric("Elapsed Time", f"{elapsed_time}:{elapsed_seconds:02d}")
            
        with col_timer3:
            st.metric("Remaining Time", f"{remaining_time}:{remaining_seconds:02d}")
        
        col_btn1, col_btn2, col_btn3, col_btn4 = st.columns(4)
        
        with col_btn1:
            if not st.session_state.game_active:
                if st.button("Start Game", use_container_width=True):
                    tm.start_game()
                    st.rerun()
            else:
                if st.session_state.game_paused:
                    if st.button("Resume Game", use_container_width=True):
                        tm.resume_game()
                        st.rerun()
                else:
                    if st.button("Pause Game", use_container_width=True):
                        tm.pause_game()
                        st.rerun()
        
        with col_btn2:
            if st.button("Reset Timer", use_container_width=True):
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
