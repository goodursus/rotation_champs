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
    
    # Recalculate ratings
    calculate_ratings()
