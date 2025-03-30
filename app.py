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
import storage

# Set page configuration
st.set_page_config(
    page_title="Rotation Players",
    page_icon="🏸",
    layout="wide"
)

# Use Streamlit's auto-refresh feature
def enable_auto_refresh():
    """
    Enables automatic page refresh with timer
    """
    # If game is active and not paused, enable auto-refresh every second
    if st.session_state.get('game_active', False) and not st.session_state.get('game_paused', True):
        time.sleep(0.1)  # Small delay to reduce load
        st.rerun()

# Initialize counter for displaying timer changes
if 'update_counter' not in st.session_state:
    st.session_state.update_counter = 0
else:
    # Increment counter on each update if game is active and not paused
    if st.session_state.get('game_active', False) and not st.session_state.get('game_paused', True):
        st.session_state.update_counter += 1

# Инициализация хранилища при запуске (перенесено в начало файла)
storage.initialize_storage()

# Инициализация session state и загрузка данных произошла в storage.initialize_storage()

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

# Initialize player matching algorithm settings
if 'matchmaking_strategy' not in st.session_state:
    st.session_state.matchmaking_strategy = 'Random Distribution'

# Проверяем, есть ли установленная active_tab
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0  # По умолчанию открываем первую вкладку

# Main application layout
st.title("Rotation Players")

# Create tabs for separating content
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Courts & Timer", "Player Statistics", "Tournament", "Leaderboard", "Court Designer"])

# Проверяем, нужно ли переключиться на другую вкладку
# Это сработает только если пользователь нажал кнопку, которая меняет active_tab
# и затем происходит rerun()

with tab1:
    # Create layout with two columns
    col1, col2 = st.columns([2, 1])

    with col1:
        # Display tournament selector at the top
        st.header("Tournament Selection")
        ca.display_tournament_selector()
        
        # Display courts with players
        st.header("Courts")
        
        # Add player matching settings
        with st.expander("Player Matching Settings"):
            st.session_state.matchmaking_strategy = st.radio(
                "Select player distribution strategy:",
                ["Random Distribution", "Skill-Based Balanced Teams"]
            )
            
            if st.session_state.matchmaking_strategy == "Skill-Based Balanced Teams":
                st.info("""
                    **Algorithm Description:** 
                    This algorithm distributes players based on their rating to create 
                    maximally balanced teams. High-rated players are distributed across 
                    courts using the "snake" method to ensure even distribution. Then 
                    within each court, players are divided into teams to minimize the 
                    difference in total team ratings.
                """)
            else:
                st.info("""
                    **Algorithm Description:** 
                    Random distribution of players across courts without considering ratings.
                """)
        
        # Check if tournament is active and has participants
        active_tournament_id = st.session_state.get('active_tournament_id')
        has_tournament_players = False
        
        if active_tournament_id is not None:
            # Find the tournament in the list
            tournament = next((t for t in st.session_state.tournaments_list if t['id'] == active_tournament_id), None)
            if tournament and 'participants' in tournament and tournament['participants']:
                has_tournament_players = True
        
        # Display courts if they exist
        if st.session_state.courts:
            ca.display_courts(st.session_state.courts, st.session_state.players_df)
        elif not has_tournament_players:
            st.warning("Please select a tournament and add participants first.")
            st.button("Distribute Players", key="btn_distribute_disabled", disabled=True, use_container_width=True)
        else:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("Distribute Players", key="btn_distribute_main", use_container_width=True):
                    st.session_state.courts = ca.distribute_players()
                    st.rerun()

        # Game timer controls
        st.header("Game Timer")
        
        # Add timer status
        timer_status = ""
        if st.session_state.game_active:
            if st.session_state.game_paused:
                timer_status = "⏸️ Paused"
            else:
                timer_status = "▶️ Active"
        else:
            timer_status = "⏹️ Not Started"
            
        st.write(f"**Timer Status:** {timer_status}")
        
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
            
            # Timer indicators
            update_count = st.session_state.get('update_counter', 0)
            reset_count = st.session_state.get('reset_counter', 0)
            
            # Add visual hint about timer state
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
                
            # Display metric with additional information
            st.metric(
                elapsed_label, 
                f"{elapsed_time}:{elapsed_seconds:02d}", 
                delta=delta_value, 
                delta_color="normal" if delta_value else "off",
                help=f"Updates: {update_count}, Resets: {reset_count}"
            )
            
        with col_timer3:
            # Show remaining time
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
        
        # Check if tournament is active
        active_tournament_id = st.session_state.get('active_tournament_id')
        tournament_active = active_tournament_id is not None
        
        # If tournament is not active, disable timer buttons with explanation
        if not tournament_active:
            st.warning("To activate the timer, you need to start a tournament first")
        
        with col_btn1:
            if not st.session_state.game_active:
                # Get tournament time status if tournament is active
                tournament_time_expired = False
                if tournament_active:
                    _, _, remaining_minutes, remaining_seconds = tr.calculate_tournament_time(active_tournament_id)
                    tournament_time_expired = remaining_minutes == 0 and remaining_seconds == 0
                
                # Disable button if tournament inactive or time expired, или после завершения игры до нажатия Rotate Players
                button_disabled = not tournament_active or tournament_time_expired or st.session_state.get('game_ended', False)
                if st.button("Start Game", key="btn_start_game", use_container_width=True, disabled=button_disabled):
                    # Сбрасываем флаг завершения игры при старте новой
                    st.session_state.game_ended = False
                    tm.start_game()
                    st.rerun()
            else:
                if st.session_state.game_paused:
                    if st.button("Resume Game", key="btn_resume_game", use_container_width=True, disabled=not tournament_active):
                        tm.resume_game()
                        st.rerun()
                else:
                    if st.button("Pause Game", key="btn_pause_game", use_container_width=True, disabled=not tournament_active):
                        tm.pause_game()
                        st.rerun()
        
        with col_btn2:
            if st.button("Reset Timer", key="btn_reset_timer", use_container_width=True, disabled=not tournament_active):
                tm.reset_game()
                st.rerun()
        
        with col_btn3:
            # Check if tournament is active and has participants
            button_disabled = False
            if active_tournament_id is None:
                button_disabled = True
            else:
                # Find the tournament in the list
                tournament = next((t for t in st.session_state.tournaments_list if t['id'] == active_tournament_id), None)
                if not tournament or 'participants' not in tournament or not tournament['participants']:
                    button_disabled = True
            
            # Проверяем, активна ли игра (не должны распределять игроков во время игры)
            is_game_active = st.session_state.get('game_active', False)
            if st.button("Distribute Players", key="distribute_btn_bottom", use_container_width=True, 
                        disabled=button_disabled or is_game_active):
                st.session_state.courts = ca.distribute_players()
                # Сбрасываем флаг завершения игры при новом распределении
                st.session_state.game_ended = False
                st.rerun()
                
        with col_btn4:
            # Only enable rotate if courts exist
            has_courts = 'courts' in st.session_state and st.session_state.courts
            # Добавляем дополнительную проверку на активную игру
            is_game_active = st.session_state.get('game_active', False)
            if st.button("Rotate Players", key="btn_rotate_players", use_container_width=True, 
                        disabled=not has_courts or is_game_active):
                # Сбрасываем флаг завершения игры, чтобы можно было запустить следующую
                st.session_state.game_ended = False
                ca.rotate_players()
                st.rerun()

    with col2:
        # Player management section
        st.header("Players")
        
        # Only show player management section if there's an active tournament or user requested it
        active_tournament_id = st.session_state.get('active_tournament_id')
        if active_tournament_id is not None or st.session_state.get('show_player_management', False):
            pm.manage_players()
        else:
            # Show button to display player management
            if st.button("Show Player Management", key="btn_show_players"):
                st.session_state.show_player_management = True
                st.rerun()

with tab2:
    # Display player statistics
    st.header("Player Statistics")
    pm.display_player_stats()

with tab3:
    # Display tournament bracket and functionality
    st.header("Tournament Mode")
    tr.display_tournament()

with tab4:
    # Display dynamic leaderboard
    st.header("Leaderboard")
    # Main leaderboard
    lb.display_leaderboard()
    
    # Animation demo
    with st.expander("Leaderboard Animation Demo"):
        lb.display_leaderboard_animation_demo()

with tab5:
    # Display court designer
    st.header("Court Designer")
    designer.display_court_designer()

# Check if timer needs to be reset (e.g., after auto-generating results)
if st.session_state.get('timer_needs_reset', False):
    # Reset flag
    st.session_state.timer_needs_reset = False
    # Reset timer
    tm.reset_game()
    # Reload page
    st.rerun()

# Disable Start Game button if tournament time has elapsed
active_tournament_id = st.session_state.get('active_tournament_id')
if active_tournament_id is not None:
    # Calculate tournament remaining time
    _, _, remaining_minutes, remaining_seconds = tr.calculate_tournament_time(active_tournament_id)
    # Disable Start Game button if time is up
    if remaining_minutes == 0 and remaining_seconds == 0:
        st.warning("Tournament time is up. Unable to start new games.")

# Show notification about generated results if it exists
if st.session_state.get('show_results_notification', False):
    # Display main notification
    st.success("Time's up! Game results have been automatically generated. Review and save them.")
    # Reset notification on next page refresh
    st.session_state.show_results_notification = False

# Сохранение данных происходит через storage.auto_save_data()

# Инициализация хранилища уже произошла в начале файла

# Автоматическое сохранение данных
storage.auto_save_data()

# Enable auto-refresh if timer is active
enable_auto_refresh()
