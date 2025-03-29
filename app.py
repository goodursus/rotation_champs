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

# Initialize session state variables if they don't exist
if 'players_df' not in st.session_state:
    # Initialize with sample players for example (14 players)
    st.session_state.players_df = pd.DataFrame({
        'id': list(range(1, 15)),
        'name': [f"Player {i}" for i in range(1, 15)],
        'email': [""] * 14,  # New field for email
        'phone': [""] * 14,  # New field for phone
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

# Initialize player matching algorithm settings
if 'matchmaking_strategy' not in st.session_state:
    st.session_state.matchmaking_strategy = 'Random Distribution'

# Main application layout
st.title("Rotation Players")

# Create tabs for separating content
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Courts & Timer", "Player Statistics", "Tournament", "Leaderboard", "Court Designer"])

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
        
        # Display courts
        if st.session_state.courts:
            ca.display_courts(st.session_state.courts, st.session_state.players_df)
        else:
            st.info("Click 'Distribute Players' to allocate players to courts.")

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

# Show notification about generated results if it exists
if st.session_state.get('show_results_notification', False):
    # Display main notification
    st.success("Time's up! Game results have been automatically generated. Review and save them.")
    # Reset notification on next page refresh
    st.session_state.show_results_notification = False

# Enable auto-refresh if timer is active
enable_auto_refresh()
