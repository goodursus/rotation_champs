import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime
import player_management as pm
import player_matching as match
import tournament as tr

def distribute_players(players_df=None):
    """
    Distribute players across courts based on selected strategy and active tournament
    
    Parameters:
    - players_df: DataFrame with player information, if None, uses tournament participants
    
    Returns:
    - List of courts with player allocations
    """
    # Check if there's an active tournament and use those players
    active_tournament_id = st.session_state.get('active_tournament_id')
    if active_tournament_id is not None:
        # Find the tournament in the list
        tournament = next((t for t in st.session_state.tournaments_list if t['id'] == active_tournament_id), None)
        
        if tournament and 'participants' in tournament and tournament['participants']:
            # Filter the players dataframe to only include participants from the tournament
            tournament_players_ids = tournament['participants']
            tournament_players_df = st.session_state.players_df[st.session_state.players_df['id'].isin(tournament_players_ids)]
            
            if tournament_players_df.empty:
                st.error("No players available in the selected tournament.")
                return []
                
            # Use the tournament players dataframe for distribution
            players_df = tournament_players_df
        else:
            st.error("No participants found in the active tournament.")
            return []
    elif players_df is None:
        # If no tournament is active and no dataframe is provided, use all players
        players_df = st.session_state.players_df
    
    # Check which player matching strategy was selected by the user
    matchmaking_strategy = st.session_state.get('matchmaking_strategy', 'Random Distribution')
    
    if matchmaking_strategy == 'Skill-Based Balanced Teams':
        # Use advanced skill-based matching algorithm
        return match.get_skill_based_courts(players_df)
    else:
        # Use random player distribution (original method)
        return random_distribute_players(players_df)

def random_distribute_players(players_df):
    """
    Distribute players randomly across courts (original algorithm)
    
    Parameters:
    - players_df: DataFrame with player information
    
    Returns:
    - List of courts with player allocations
    """
    # Get player IDs
    player_ids = players_df['id'].tolist()
    
    # Shuffle player IDs randomly
    random.shuffle(player_ids)
    
    # Calculate number of courts needed
    num_players = len(player_ids)
    num_full_courts = num_players // 4
    
    # Check if we need a rest court
    has_rest_court = num_players % 4 != 0
    rest_players = player_ids[num_full_courts * 4:] if has_rest_court else []
    
    # Initialize courts list
    courts = []
    
    # Allocate players to full courts
    for i in range(num_full_courts):
        start_idx = i * 4
        court_players = player_ids[start_idx:start_idx + 4]
        
        court = {
            'court_number': i + 1,
            'team_a': court_players[:2],
            'team_b': court_players[2:],
            'is_rest': False
        }
        courts.append(court)
    
    # Create rest court if needed
    if has_rest_court:
        court = {
            'court_number': num_full_courts + 1,
            'team_a': rest_players,
            'team_b': [],
            'is_rest': True
        }
        courts.append(court)
    
    return courts

def display_courts(courts, players_df):
    """
    Display courts with player allocations and score inputs
    
    Parameters:
    - courts: List of court dictionaries
    - players_df: DataFrame with player information
    """
    # Отображаем информацию об активном турнире сверху, если есть
    active_tournament_id = st.session_state.get('active_tournament_id')
    if active_tournament_id is not None and 'tournaments_list' in st.session_state:
        # Находим активный турнир
        tournament = next((t for t in st.session_state.tournaments_list if t['id'] == active_tournament_id), None)
        if tournament:
            # Создаем контейнер для сводной информации о турнире
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    # Базовая информация о турнире
                    st.markdown(f"### Активный турнир: {tournament['name']}")
                    
                    # Прогресс игр
                    current_game = tournament.get('current_game', 0)
                    total_games = tournament.get('total_games', 0)
                    st.markdown(f"**Игра:** {current_game + 1}/{total_games}")
                
                with col2:
                    # Информация о времени турнира
                    import tournament as tr
                    elapsed_minutes, elapsed_seconds, remaining_minutes, remaining_seconds = tr.calculate_tournament_time(active_tournament_id)
                    
                    # Статус турнира
                    is_paused = tournament.get('pause_time') is not None
                    status_text = "⏸️ На паузе" if is_paused else "▶️ Активен"
                    st.markdown(f"**Статус:** {status_text}")
                    
                    # Время
                    st.markdown(f"**Время турнира:** {elapsed_minutes:02d}:{elapsed_seconds:02d}")
                    st.markdown(f"**Осталось:** {remaining_minutes:02d}:{remaining_seconds:02d}")
                
                with col3:
                    # Кнопки управления турниром
                    if is_paused:
                        if st.button("Возобновить", key="resume_tournament_main"):
                            tr.resume_tournament_timer(active_tournament_id)
                            st.rerun()
                    else:
                        if st.button("Пауза", key="pause_tournament_main"):
                            tr.pause_tournament_timer(active_tournament_id)
                            st.rerun()
                            
                    # Кнопка для завершения игры
                    if st.button("➡️ Следующая игра", key="next_game"):
                        if current_game < total_games - 1:
                            # Увеличиваем счетчик текущей игры
                            tournament_idx = next((i for i, t in enumerate(st.session_state.tournaments_list) 
                                                if t['id'] == active_tournament_id), None)
                            if tournament_idx is not None:
                                st.session_state.tournaments_list[tournament_idx]['current_game'] += 1
                        st.rerun()
    
    # Calculate number of columns for layout
    num_courts = len(courts)
    cols_per_row = 3
    num_rows = (num_courts + cols_per_row - 1) // cols_per_row
    
    # Create rows and columns for courts display
    for row in range(num_rows):
        cols = st.columns(cols_per_row)
        
        for col in range(cols_per_row):
            court_idx = row * cols_per_row + col
            
            if court_idx < num_courts:
                court = courts[court_idx]
                
                # Проверяем, есть ли результат для этого корта
                team_a_score_key = f"direct_team_a_score_{court_idx}"
                team_b_score_key = f"direct_team_b_score_{court_idx}"
                
                team_a_score = st.session_state.get(team_a_score_key, None)
                team_b_score = st.session_state.get(team_b_score_key, None)
                
                # Определяем, есть ли победитель и проигравший
                winner_bg = "#e6ffe6"  # светло-зеленый для победителей
                loser_bg = "#fff9e0"   # светло-желтый для проигравших
                default_bg = "#f0f0f0" # стандартный фон
                rest_bg = "#e0f7fa"    # фон для отдыха
                
                # Выбираем цвет фона
                bg_color = rest_bg if court['is_rest'] else default_bg
                
                # Проверяем результаты и устанавливаем фон
                team_a_style = ""
                team_b_style = ""
                
                if not court['is_rest'] and team_a_score is not None and team_b_score is not None:
                    if team_a_score > team_b_score:
                        team_a_style = f"background-color: {winner_bg}; padding: 8px; border-radius: 4px; color: #004d00;" 
                        team_b_style = f"background-color: {loser_bg}; padding: 8px; border-radius: 4px; color: #664d00;"
                    elif team_b_score > team_a_score:
                        team_a_style = f"background-color: {loser_bg}; padding: 8px; border-radius: 4px; color: #664d00;"
                        team_b_style = f"background-color: {winner_bg}; padding: 8px; border-radius: 4px; color: #004d00;"
                
                with cols[col]:
                    with st.container(border=True):
                        # Court header
                        if court['is_rest']:
                            st.subheader(f"Rest Court {court['court_number']}")
                        else:
                            st.subheader(f"Court {court['court_number']}")
                            
                            # If skill-based team balancing is selected, show balance information
                            if st.session_state.get('matchmaking_strategy', '') == 'Skill-Based Balanced Teams':
                                # Calculate team balance
                                team_a_rating = sum(players_df.loc[players_df['id'] == player_id, 'rating'].values[0] 
                                                  for player_id in court['team_a'])
                                team_b_rating = sum(players_df.loc[players_df['id'] == player_id, 'rating'].values[0] 
                                                  for player_id in court['team_b'])
                                
                                # Rating difference
                                rating_diff = abs(team_a_rating - team_b_rating)
                                
                                # Determine color based on difference
                                if rating_diff < 0.5:
                                    balance_color = "green"
                                    balance_text = "Excellent Balance"
                                elif rating_diff < 1.5:
                                    balance_color = "orange"
                                    balance_text = "Good Balance"
                                else:
                                    balance_color = "red"
                                    balance_text = "Imbalanced"
                                
                                # Display balance information
                                st.markdown(f'<span style="color:{balance_color};font-size:small;">{balance_text} (difference: {rating_diff:.2f})</span>', unsafe_allow_html=True)
                        
                        # Display teams
                        if not court['is_rest']:
                            # Get player names for display
                            team_a_names = [players_df.loc[players_df['id'] == player_id, 'name'].values[0] 
                                           for player_id in court['team_a']]
                            team_b_names = [players_df.loc[players_df['id'] == player_id, 'name'].values[0] 
                                           for player_id in court['team_b']]
                            
                            # Используем HTML для подсветки победителей/проигравших
                            if team_a_style:
                                st.markdown(f'<div style="{team_a_style}"><strong>Team A</strong></div>', unsafe_allow_html=True)
                            else:
                                st.markdown("**Team A**")
                            
                            # Check if we need to display ratings
                            show_ratings = st.session_state.get('matchmaking_strategy', '') == 'Skill-Based Balanced Teams'
                            
                            # Игроки команды A с подсветкой если есть результат
                            team_a_div = '<div style="{}">'.format(team_a_style) if team_a_style else '<div>'
                            for i, player_id in enumerate(court['team_a']):
                                if i < len(team_a_names):
                                    player_name = team_a_names[i]
                                    if show_ratings:
                                        # Get player rating
                                        player_rating = players_df.loc[players_df['id'] == player_id, 'rating'].values[0]
                                        if team_a_style:
                                            st.markdown(f'{team_a_div}- {player_name} <em>(rating: {player_rating:.2f})</em></div>', unsafe_allow_html=True)
                                        else:
                                            st.write(f"- {player_name} *(rating: {player_rating:.2f})*")
                                    else:
                                        if team_a_style:
                                            st.markdown(f'{team_a_div}- {player_name}</div>', unsafe_allow_html=True)
                                        else:
                                            st.write(f"- {player_name}")
                                
                            # Проверяем, есть ли автоматически сгенерированные результаты для этого корта
                            auto_score_a = None
                            auto_score_b = None
                            
                            if 'pending_results' in st.session_state and st.session_state.pending_results:
                                for result in st.session_state.pending_results:
                                    if result['court_idx'] == court_idx:
                                        auto_score_a = result['team_a_score']
                                        auto_score_b = result['team_b_score']
                                        break
                            
                            # Счет команды A отдельно (с предварительно заданным значением, если есть)
                            if f"direct_team_a_score_{court_idx}" not in st.session_state and auto_score_a is not None:
                                team_a_score = st.number_input(
                                    "Team A Score", 
                                    min_value=0, 
                                    max_value=99,
                                    value=auto_score_a,
                                    key=f"direct_team_a_score_{court_idx}"
                                )
                            else:
                                team_a_score = st.number_input(
                                    "Team A Score", 
                                    min_value=0, 
                                    max_value=99,
                                    key=f"direct_team_a_score_{court_idx}"
                                )
                            
                            # Команда B с подсветкой
                            if team_b_style:
                                st.markdown(f'<div style="{team_b_style}"><strong>Team B</strong></div>', unsafe_allow_html=True)
                            else:
                                st.markdown("**Team B**")
                            
                            # Игроки команды B с подсветкой
                            team_b_div = '<div style="{}">'.format(team_b_style) if team_b_style else '<div>'
                            for i, player_id in enumerate(court['team_b']):
                                if i < len(team_b_names):
                                    player_name = team_b_names[i]
                                    if show_ratings:
                                        # Get player rating
                                        player_rating = players_df.loc[players_df['id'] == player_id, 'rating'].values[0]
                                        if team_b_style:
                                            st.markdown(f'{team_b_div}- {player_name} <em>(rating: {player_rating:.2f})</em></div>', unsafe_allow_html=True)
                                        else:
                                            st.write(f"- {player_name} *(rating: {player_rating:.2f})*")
                                    else:
                                        if team_b_style:
                                            st.markdown(f'{team_b_div}- {player_name}</div>', unsafe_allow_html=True)
                                        else:
                                            st.write(f"- {player_name}")
                                
                            # Счет команды B отдельно (с предварительно заданным значением, если есть)
                            if f"direct_team_b_score_{court_idx}" not in st.session_state and auto_score_b is not None:
                                team_b_score = st.number_input(
                                    "Team B Score", 
                                    min_value=0, 
                                    max_value=99,
                                    value=auto_score_b,
                                    key=f"direct_team_b_score_{court_idx}"
                                )
                            else:
                                team_b_score = st.number_input(
                                    "Team B Score", 
                                    min_value=0, 
                                    max_value=99,
                                    key=f"direct_team_b_score_{court_idx}"
                                )
                                
                            # Если есть уведомление о сгенерированных результатах
                            if st.session_state.get('show_results_notification', False) and auto_score_a is not None and auto_score_b is not None:
                                st.success(f"Automatically generated result: {auto_score_a} - {auto_score_b}")
                            
                            # Submit button for this court
                            if st.button("Save Result", key=f"save_result_{court_idx}"):
                                # Update player statistics
                                import player_management as pm
                                # Use values from Streamlit states for reliability
                                team_a_score = st.session_state.get(f"direct_team_a_score_{court_idx}", 0)
                                team_b_score = st.session_state.get(f"direct_team_b_score_{court_idx}", 0)
                                pm.update_player_stats(court_idx, team_a_score, team_b_score)
                                st.success("Score saved!")
                                
                        else:
                            # For rest court, just list all players
                            st.markdown("**Resting Players**")
                            for player_id in court['team_a']:
                                player_name = players_df.loc[players_df['id'] == player_id, 'name'].values[0]
                                st.write(f"- {player_name}")

def record_game_results():
    """
    Allow recording game results for each court
    """
    # Create a form for submitting game results
    with st.form(key="game_results_form"):
        for i, court in enumerate(st.session_state.courts):
            if not court['is_rest']:
                st.subheader(f"Court {court['court_number']} Results")
                
                # Get player names for display
                team_a_names = [st.session_state.players_df.loc[st.session_state.players_df['id'] == player_id, 'name'].values[0] 
                                for player_id in court['team_a']]
                team_b_names = [st.session_state.players_df.loc[st.session_state.players_df['id'] == player_id, 'name'].values[0] 
                                for player_id in court['team_b']]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**Team A**: {', '.join(team_a_names)}")
                    team_a_score = st.number_input(
                        "Score", 
                        min_value=0, 
                        max_value=99,
                        key=f"team_a_score_{i}"
                    )
                
                with col2:
                    st.markdown(f"**Team B**: {', '.join(team_b_names)}")
                    team_b_score = st.number_input(
                        "Score", 
                        min_value=0, 
                        max_value=99,
                        key=f"team_b_score_{i}"
                    )
                
                st.divider()
        
        # Submit button for all results
        submit_button = st.form_submit_button("Submit Game Results")
        
        if submit_button:
            # Process results for each court
            for i, court in enumerate(st.session_state.courts):
                if not court['is_rest']:
                    team_a_score = st.session_state[f"team_a_score_{i}"]
                    team_b_score = st.session_state[f"team_b_score_{i}"]
                    
                    # Update player statistics
                    pm.update_player_stats(i, team_a_score, team_b_score)
            
            st.success("Game results recorded successfully!")

def display_tournament_selector():
    """
    Display tournament selector and management on the Courts & Timer tab
    """
    st.subheader("Tournament Selection")
    
    # Initialize tournament list if not exist
    if 'tournaments_list' not in st.session_state:
        st.session_state.tournaments_list = []
    
    if not st.session_state.tournaments_list:
        st.warning("No tournaments available. Please create a tournament in the Tournament tab first.")
        return
    
    # Get active tournament if exists
    active_tournament_id = st.session_state.get('active_tournament_id')
    
    # Create list of available tournaments
    tournaments_for_selection = []
    
    # First add active tournament if exists
    if active_tournament_id is not None:
        active_tournament = next((t for t in st.session_state.tournaments_list if t['id'] == active_tournament_id), None)
        if active_tournament:
            tournaments_for_selection.append(f"{active_tournament['id']} - {active_tournament['name']} (Active)")
    
    # Then add planned tournaments
    for tournament in st.session_state.tournaments_list:
        if tournament['status'] == 'planned':
            tournaments_for_selection.append(f"{tournament['id']} - {tournament['name']}")
    
    # Select tournament from list
    selected_tournament_str = st.selectbox(
        "Select Tournament", 
        tournaments_for_selection,
        index=0 if active_tournament_id is not None else None,
        key="tournament_selector"
    )
    
    if selected_tournament_str:
        # Extract ID from selected string
        tournament_id = int(selected_tournament_str.split(' - ')[0])
        tournament = next((t for t in st.session_state.tournaments_list if t['id'] == tournament_id), None)
        
        if tournament:
            # Display tournament information
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Tournament:** {tournament['name']}")
                st.markdown(f"**Date:** {tournament['date']}")
                
                # Display tournament status
                status_map = {
                    'planned': '🔄 Planned',
                    'active': '▶️ Active',
                    'completed': '✅ Completed'
                }
                status_display = status_map.get(tournament['status'], tournament['status'])
                st.markdown(f"**Status:** {status_display}")
            
            with col2:
                st.markdown(f"**Duration:** {tournament['duration_minutes']} minutes")
                st.markdown(f"**Game Duration:** {tournament['game_duration_minutes']} minutes")
                st.markdown(f"**Players Limit:** {tournament['players_count']} players")
            
            # Show start tournament button if not active
            if tournament['status'] == 'planned':
                # Check if there's already an active tournament
                if active_tournament_id is not None:
                    st.warning("Another tournament is active. Please complete it before starting a new one.")
                else:
                    # Select tournament participants from all players
                    st.subheader("Select Tournament Participants")
                    
                    # Get list of all players
                    players_df = st.session_state.players_df
                    
                    # Create multiselect for player selection
                    selected_players = st.multiselect(
                        "Select Players",
                        options=players_df['id'].tolist(),
                        format_func=lambda x: players_df.loc[players_df['id'] == x, 'name'].values[0],
                        key="selected_tournament_players"
                    )
                    
                    # Show selected players count
                    st.write(f"Selected: {len(selected_players)}/{tournament['players_count']} players")
                    
                    # Button to start tournament
                    if st.button("Start Tournament", key="start_tournament_btn"):
                        if len(selected_players) > tournament['players_count']:
                            st.error(f"Too many players selected. Maximum is {tournament['players_count']}.")
                        elif len(selected_players) < 4:
                            st.error("At least 4 players are required to start a tournament.")
                        else:
                            # Set game duration
                            st.session_state.game_duration = tournament['game_duration_minutes']
                            
                            # Start tournament timer
                            tr.start_tournament_timer(tournament_id)
                            
                            # Save selected players for this tournament
                            tournament_idx = next((i for i, t in enumerate(st.session_state.tournaments_list) 
                                                if t['id'] == tournament_id), None)
                            if tournament_idx is not None:
                                if 'participants' not in st.session_state.tournaments_list[tournament_idx]:
                                    st.session_state.tournaments_list[tournament_idx]['participants'] = []
                                st.session_state.tournaments_list[tournament_idx]['participants'] = selected_players
                            
                            # Reload page
                            st.rerun()
            elif tournament['status'] == 'active':
                # Display active tournament information
                st.subheader("Tournament Progress")
                
                # Display timer
                elapsed_minutes, elapsed_seconds, remaining_minutes, remaining_seconds = tr.calculate_tournament_time(tournament_id)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Elapsed Time", f"{elapsed_minutes:02d}:{elapsed_seconds:02d}")
                
                with col2:
                    st.metric("Remaining Time", f"{remaining_minutes:02d}:{remaining_seconds:02d}")
                
                with col3:
                    # Display current game
                    current_game = tournament.get('current_game', 0)
                    total_games = tournament.get('total_games', 0)
                    st.metric("Game", f"{current_game + 1}/{total_games}")
                
                # Tournament control buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    is_paused = tournament.get('pause_time') is not None
                    if is_paused:
                        if st.button("Resume Tournament", key="resume_tournament_btn"):
                            tr.resume_tournament_timer(tournament_id)
                            st.rerun()
                    else:
                        if st.button("Pause Tournament", key="pause_tournament_btn"):
                            tr.pause_tournament_timer(tournament_id)
                            st.rerun()
                
                with col2:
                    if st.button("Complete Tournament", key="complete_tournament_btn"):
                        # Find tournament index
                        tournament_idx = next((i for i, t in enumerate(st.session_state.tournaments_list) 
                                            if t['id'] == tournament_id), None)
                        if tournament_idx is not None:
                            # Change status to completed
                            st.session_state.tournaments_list[tournament_idx]['status'] = 'completed'
                            # Reset active tournament
                            st.session_state.active_tournament_id = None
                            st.rerun()
                
                # Display participants list
                if 'participants' in tournament:
                    st.subheader("Tournament Participants")
                    
                    participants = tournament['participants']
                    if participants:
                        # Create DataFrame for display
                        participants_data = []
                        for player_id in participants:
                            player_row = st.session_state.players_df.loc[st.session_state.players_df['id'] == player_id].iloc[0]
                            participants_data.append({
                                'id': player_id,
                                'name': player_row['name'],
                                'rating': player_row['rating']
                            })
                        
                        participants_df = pd.DataFrame(participants_data)
                        
                        # Sort by rating
                        participants_df = participants_df.sort_values(by='rating', ascending=False)
                        
                        # Display table
                        st.dataframe(
                            participants_df,
                            column_config={
                                'id': 'ID',
                                'name': 'Player Name',
                                'rating': st.column_config.NumberColumn(
                                    'Rating',
                                    format="%.2f"
                                )
                            },
                            use_container_width=True,
                            hide_index=True
                        )

def rotate_players():
    """
    Rotate players between courts after a game
    
    This implements a rotation strategy based on the selected matchmaking approach.
    """
    if not st.session_state.courts:
        return
    
    # Check which player matching strategy was selected by the user
    matchmaking_strategy = st.session_state.get('matchmaking_strategy', 'Random Distribution')
    
    if matchmaking_strategy == 'Skill-Based Balanced Teams':
        # Use skill-based optimized rotation
        st.session_state.courts = match.get_optimized_rotation(
            st.session_state.courts, 
            st.session_state.players_df
        )
    else:
        # Use random rotation (original method)
        random_rotate_players()

def random_rotate_players():
    """
    Rotate players randomly between courts after a game (original method)
    """
    courts = st.session_state.courts
    
    # Collect all player IDs
    all_players = []
    for court in courts:
        all_players.extend(court['team_a'])
        all_players.extend(court['team_b'])
    
    # Shuffle and redistribute
    random.shuffle(all_players)
    
    # Recreate courts with the new distribution
    new_courts = []
    
    num_players = len(all_players)
    num_full_courts = num_players // 4
    
    # Check if we need a rest court
    has_rest_court = num_players % 4 != 0
    rest_players = all_players[num_full_courts * 4:] if has_rest_court else []
    
    # Allocate players to full courts
    for i in range(num_full_courts):
        start_idx = i * 4
        court_players = all_players[start_idx:start_idx + 4]
        
        court = {
            'court_number': i + 1,
            'team_a': court_players[:2],
            'team_b': court_players[2:],
            'is_rest': False
        }
        new_courts.append(court)
    
    # Create rest court if needed
    if has_rest_court:
        court = {
            'court_number': num_full_courts + 1,
            'team_a': rest_players,
            'team_b': [],
            'is_rest': True
        }
        new_courts.append(court)
    
    st.session_state.courts = new_courts
