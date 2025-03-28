import streamlit as st
import pandas as pd
import numpy as np

def manage_players():
    """
    Function to manage players - add, edit and delete players
    """
    # Display the players table with editable cells
    edited_df = st.data_editor(
        st.session_state.players_df[['name', 'wins', 'losses', 'points_difference', 'rating']],
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "name": "Player Name",
            "wins": "Wins",
            "losses": "Losses",
            "points_difference": "Points Difference",
            "rating": st.column_config.NumberColumn(
                "Rating",
                help="Player rating based on performance",
                format="%.2f",
                step=0.01,
            ),
        },
        disabled=["wins", "losses", "points_difference", "rating"],
    )
    
    # Handle adding/removing players
    if edited_df.shape[0] != st.session_state.players_df.shape[0]:
        if edited_df.shape[0] > st.session_state.players_df.shape[0]:
            # Players added
            num_new_players = edited_df.shape[0] - st.session_state.players_df.shape[0]
            new_ids = list(range(st.session_state.players_df['id'].max() + 1, 
                                  st.session_state.players_df['id'].max() + 1 + num_new_players))
            
            new_players = pd.DataFrame({
                'id': new_ids,
                'name': edited_df.iloc[-num_new_players:]['name'].values,
                'wins': [0] * num_new_players,
                'losses': [0] * num_new_players,
                'points_difference': [0] * num_new_players,
                'rating': [0] * num_new_players
            })
            
            # Инициализируем историю рейтинга для новых игроков
            if 'rating_history' not in st.session_state:
                st.session_state.rating_history = {}
                
            # Получаем текущее время для записи в историю
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
            # Создаем начальную запись рейтинга для каждого нового игрока
            for player_id in new_ids:
                if player_id not in st.session_state.rating_history:
                    st.session_state.rating_history[player_id] = []
                    
                st.session_state.rating_history[player_id].append({
                    'timestamp': timestamp,
                    'rating': 0.0
                })
            
            st.session_state.players_df = pd.concat([st.session_state.players_df, new_players], ignore_index=True)
        else:
            # Players removed
            # Find names that were in the original but not in the edited
            original_names = set(st.session_state.players_df['name'])
            edited_names = set(edited_df['name'])
            removed_names = original_names - edited_names
            
            # Remove those players
            st.session_state.players_df = st.session_state.players_df[~st.session_state.players_df['name'].isin(removed_names)]
            
    # Update player names
    st.session_state.players_df['name'] = edited_df['name'].values
    
    # Recalculate ratings after changes
    calculate_ratings()

def calculate_ratings():
    """
    Calculate player ratings based on wins, losses and point differences
    """
    if len(st.session_state.players_df) > 0:
        # Сохраняем предыдущие рейтинги для отслеживания изменений
        old_ratings = {}
        if 'players_df' in st.session_state:
            for _, row in st.session_state.players_df.iterrows():
                old_ratings[row['id']] = row['rating']
        
        # Simple rating formula: (wins - losses) + (points_difference / 100)
        st.session_state.players_df['rating'] = (
            st.session_state.players_df['wins'] - 
            st.session_state.players_df['losses'] + 
            st.session_state.players_df['points_difference'] / 100
        )
        
        # Обновляем историю рейтингов для каждого игрока
        if 'rating_history' not in st.session_state:
            st.session_state.rating_history = {}
            
        # Получаем текущее время для записи в историю
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        # Обновляем историю рейтингов для каждого игрока
        for _, row in st.session_state.players_df.iterrows():
            player_id = row['id']
            current_rating = row['rating']
            
            # Пропускаем, если рейтинг не изменился
            if player_id in old_ratings and abs(old_ratings[player_id] - current_rating) < 0.001:
                continue
                
            # Создаем запись для игрока, если ее еще нет
            if player_id not in st.session_state.rating_history:
                st.session_state.rating_history[player_id] = []
                
            # Добавляем новую запись в историю
            st.session_state.rating_history[player_id].append({
                'timestamp': timestamp,
                'rating': current_rating
            })

def display_player_stats():
    """
    Display player statistics sorted by rating
    """
    # Sort players by rating
    sorted_df = st.session_state.players_df.sort_values(by='rating', ascending=False).reset_index(drop=True)
    
    # Add rank column
    sorted_df.insert(0, 'rank', range(1, len(sorted_df) + 1))
    
    # Display the sorted stats
    st.dataframe(
        sorted_df[['rank', 'name', 'wins', 'losses', 'points_difference', 'rating']],
        use_container_width=True,
        column_config={
            "rank": "Rank",
            "name": "Player Name",
            "wins": "Wins",
            "losses": "Losses",
            "points_difference": "Points Difference",
            "rating": st.column_config.NumberColumn(
                "Rating",
                help="Player rating based on performance",
                format="%.2f",
            ),
        },
        hide_index=True,
    )

def update_player_stats(court_idx, team_a_score, team_b_score):
    """
    Update player statistics based on game results
    
    Parameters:
    - court_idx: Index of the court
    - team_a_score: Score of team A
    - team_b_score: Score of team B
    """
    court = st.session_state.courts[court_idx]
    
    # Check if this is a rest court
    if court['is_rest']:
        return
    
    team_a_ids = court['team_a']
    team_b_ids = court['team_b']
    
    score_diff = team_a_score - team_b_score
    
    # Update stats for team A
    for player_id in team_a_ids:
        player_idx = st.session_state.players_df.loc[st.session_state.players_df['id'] == player_id].index[0]
        
        if team_a_score > team_b_score:
            st.session_state.players_df.at[player_idx, 'wins'] += 1
        else:
            st.session_state.players_df.at[player_idx, 'losses'] += 1
            
        st.session_state.players_df.at[player_idx, 'points_difference'] += score_diff
    
    # Update stats for team B
    for player_id in team_b_ids:
        player_idx = st.session_state.players_df.loc[st.session_state.players_df['id'] == player_id].index[0]
        
        if team_b_score > team_a_score:
            st.session_state.players_df.at[player_idx, 'wins'] += 1
        else:
            st.session_state.players_df.at[player_idx, 'losses'] += 1
            
        st.session_state.players_df.at[player_idx, 'points_difference'] -= score_diff
    
    # Сохраняем историю игры
    save_game_history(court_idx, court, team_a_score, team_b_score)
    
    # Recalculate ratings
    calculate_ratings()

def save_game_history(court_idx, court, team_a_score, team_b_score):
    """
    Сохраняет историю игр для будущего анализа
    
    Parameters:
    - court_idx: Индекс корта
    - court: Информация о корте
    - team_a_score: Счет команды A
    - team_b_score: Счет команды B
    """
    # Проверяем, есть ли структура для истории
    if 'game_history' not in st.session_state:
        st.session_state.game_history = []
    
    # Определяем, в рамках какого турнира проводится игра
    tournament_info = {}
    active_tournament_id = st.session_state.get('active_tournament_id')
    
    if active_tournament_id is not None and 'tournaments_list' in st.session_state:
        # Находим активный турнир
        tournament = next((t for t in st.session_state.tournaments_list if t['id'] == active_tournament_id), None)
        if tournament:
            tournament_info = {
                'tournament_id': tournament['id'],
                'tournament_name': tournament['name'],
                'game_number': tournament.get('current_game', 0) + 1,
                'total_games': tournament.get('total_games', 0)
            }
    
    # Создаем запись о новой игре
    from datetime import datetime
    
    game_record = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'court_number': court.get('court_number', court_idx + 1),
        'team_a_players': court['team_a'],
        'team_b_players': court['team_b'],
        'team_a_score': team_a_score,
        'team_b_score': team_b_score,
        'tournament': tournament_info
    }
    
    # Добавляем запись в историю
    st.session_state.game_history.append(game_record)
    
    # Если история турнира еще не инициализирована
    if 'tournament_history' not in st.session_state:
        st.session_state.tournament_history = {}
    
    # Если есть информация о турнире, добавляем эту игру в историю турнира
    if tournament_info and 'tournament_id' in tournament_info:
        tournament_id = tournament_info['tournament_id']
        
        # Создаем запись для турнира, если её еще нет
        if tournament_id not in st.session_state.tournament_history:
            st.session_state.tournament_history[tournament_id] = {
                'tournament_info': tournament_info,
                'games': [],
                'player_stats': {}  # Для сохранения статистики игроков в этом турнире
            }
        
        # Добавляем игру в историю турнира
        st.session_state.tournament_history[tournament_id]['games'].append(game_record)
        
        # Обновляем статистику игроков в этом турнире
        # Для команды A
        for player_id in court['team_a']:
            if player_id not in st.session_state.tournament_history[tournament_id]['player_stats']:
                st.session_state.tournament_history[tournament_id]['player_stats'][player_id] = {
                    'wins': 0, 'losses': 0, 'points_scored': 0, 'points_conceded': 0
                }
            
            player_stats = st.session_state.tournament_history[tournament_id]['player_stats'][player_id]
            
            if team_a_score > team_b_score:
                player_stats['wins'] += 1
            else:
                player_stats['losses'] += 1
                
            player_stats['points_scored'] += team_a_score
            player_stats['points_conceded'] += team_b_score
        
        # Для команды B
        for player_id in court['team_b']:
            if player_id not in st.session_state.tournament_history[tournament_id]['player_stats']:
                st.session_state.tournament_history[tournament_id]['player_stats'][player_id] = {
                    'wins': 0, 'losses': 0, 'points_scored': 0, 'points_conceded': 0
                }
            
            player_stats = st.session_state.tournament_history[tournament_id]['player_stats'][player_id]
            
            if team_b_score > team_a_score:
                player_stats['wins'] += 1
            else:
                player_stats['losses'] += 1
                
            player_stats['points_scored'] += team_b_score
            player_stats['points_conceded'] += team_a_score
