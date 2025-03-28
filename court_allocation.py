import streamlit as st
import pandas as pd
import numpy as np
import random
import player_management as pm
import player_matching as match

def distribute_players(players_df):
    """
    Distribute players across courts based on selected strategy
    
    Parameters:
    - players_df: DataFrame with player information
    
    Returns:
    - List of courts with player allocations
    """
    # Проверяем, какую стратегию подбора игроков выбрал пользователь
    matchmaking_strategy = st.session_state.get('matchmaking_strategy', 'Случайное распределение')
    
    if matchmaking_strategy == 'Сбалансированные команды по навыкам':
        # Используем продвинутый алгоритм подбора на основе навыков
        return match.get_skill_based_courts(players_df)
    else:
        # Используем случайное распределение игроков (оригинальный метод)
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
                
                # Choose background color - rest court is different
                bg_color = "#f0f0f0" if not court['is_rest'] else "#e0f7fa"
                
                with cols[col]:
                    with st.container(border=True):
                        # Court header
                        if court['is_rest']:
                            st.subheader(f"Rest Court {court['court_number']}")
                        else:
                            st.subheader(f"Court {court['court_number']}")
                            
                            # Если выбран алгоритм сбалансированных команд, показываем информацию о балансе
                            if st.session_state.get('matchmaking_strategy', '') == 'Сбалансированные команды по навыкам':
                                # Рассчитываем баланс команд
                                team_a_rating = sum(players_df.loc[players_df['id'] == player_id, 'rating'].values[0] 
                                                  for player_id in court['team_a'])
                                team_b_rating = sum(players_df.loc[players_df['id'] == player_id, 'rating'].values[0] 
                                                  for player_id in court['team_b'])
                                
                                # Разница в рейтинге
                                rating_diff = abs(team_a_rating - team_b_rating)
                                
                                # Определяем цвет на основе разницы
                                if rating_diff < 0.5:
                                    balance_color = "green"
                                    balance_text = "Отличный баланс"
                                elif rating_diff < 1.5:
                                    balance_color = "orange"
                                    balance_text = "Хороший баланс"
                                else:
                                    balance_color = "red"
                                    balance_text = "Дисбаланс"
                                
                                # Отображаем информацию о балансе
                                st.markdown(f'<span style="color:{balance_color};font-size:small;">{balance_text} (разница: {rating_diff:.2f})</span>', unsafe_allow_html=True)
                        
                        # Display teams
                        if not court['is_rest']:
                            # Get player names for display
                            team_a_names = [players_df.loc[players_df['id'] == player_id, 'name'].values[0] 
                                           for player_id in court['team_a']]
                            team_b_names = [players_df.loc[players_df['id'] == player_id, 'name'].values[0] 
                                           for player_id in court['team_b']]
                            
                            # Используем HTML для размещения счета рядом с именем игрока
                            st.markdown("**Team A**")
                            
                            # Проверяем, нужно ли отображать рейтинги
                            show_ratings = st.session_state.get('matchmaking_strategy', '') == 'Сбалансированные команды по навыкам'
                            
                            # Игроки команды A
                            for i, player_id in enumerate(court['team_a']):
                                if i < len(team_a_names):
                                    player_name = team_a_names[i]
                                    if show_ratings:
                                        # Получаем рейтинг игрока
                                        player_rating = players_df.loc[players_df['id'] == player_id, 'rating'].values[0]
                                        st.write(f"- {player_name} *(рейтинг: {player_rating:.2f})*")
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
                            
                            # Команда B
                            st.markdown("**Team B**")
                            
                            # Игроки команды B
                            for i, player_id in enumerate(court['team_b']):
                                if i < len(team_b_names):
                                    player_name = team_b_names[i]
                                    if show_ratings:
                                        # Получаем рейтинг игрока
                                        player_rating = players_df.loc[players_df['id'] == player_id, 'rating'].values[0]
                                        st.write(f"- {player_name} *(рейтинг: {player_rating:.2f})*")
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
                                st.success(f"Автоматически сгенерирован результат: {auto_score_a} - {auto_score_b}")
                            
                            # Submit button for this court
                            if st.button("Save Result", key=f"save_result_{court_idx}"):
                                # Update player statistics
                                import player_management as pm
                                # Используем значения из Streamlit states для надежности
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

def rotate_players():
    """
    Rotate players between courts after a game
    
    This implements a rotation strategy based on the selected matchmaking approach.
    """
    if not st.session_state.courts:
        return
    
    # Проверяем, какую стратегию подбора игроков выбрал пользователь
    matchmaking_strategy = st.session_state.get('matchmaking_strategy', 'Случайное распределение')
    
    if matchmaking_strategy == 'Сбалансированные команды по навыкам':
        # Используем оптимизированную ротацию на основе навыков
        st.session_state.courts = match.get_optimized_rotation(
            st.session_state.courts, 
            st.session_state.players_df
        )
    else:
        # Используем случайную ротацию (оригинальный метод)
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
