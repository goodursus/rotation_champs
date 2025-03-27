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

def pause_game():
    """
    Pause the current game
    """
    if st.session_state.game_active and not st.session_state.game_paused:
        st.session_state.game_paused = True
        st.session_state.pause_time = datetime.now()

def resume_game():
    """
    Resume a paused game
    """
    if st.session_state.game_active and st.session_state.game_paused:
        # Calculate how long the game was paused
        pause_duration = (datetime.now() - st.session_state.pause_time).total_seconds()
        st.session_state.elapsed_pause_time += pause_duration
        st.session_state.game_paused = False

def reset_game():
    """
    Reset the game timer
    """
    st.session_state.game_active = False
    st.session_state.game_paused = False
    st.session_state.start_time = None
    st.session_state.pause_time = None
    st.session_state.elapsed_pause_time = 0

def calculate_game_time():
    """
    Calculate elapsed and remaining game time
    
    Returns:
    - elapsed_minutes: Minutes elapsed since game started
    - remaining_minutes: Minutes remaining in the game
    """
    if not st.session_state.game_active:
        return 0, st.session_state.game_duration
    
    if st.session_state.game_paused:
        # If game is paused, calculate elapsed time up to when it was paused
        elapsed_seconds = (st.session_state.pause_time - st.session_state.start_time).total_seconds() - st.session_state.elapsed_pause_time
    else:
        # Calculate elapsed time considering any pauses
        elapsed_seconds = (datetime.now() - st.session_state.start_time).total_seconds() - st.session_state.elapsed_pause_time
    
    # Convert to minutes
    elapsed_minutes = round(elapsed_seconds / 60, 1)
    
    # Calculate remaining time
    remaining_minutes = max(0, round(st.session_state.game_duration - elapsed_minutes, 1))
    
    return elapsed_minutes, remaining_minutes
