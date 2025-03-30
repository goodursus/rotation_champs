import streamlit as st
import pandas as pd
import numpy as np
import storage
from datetime import datetime
import random

def manage_players():
    """
    Function to manage players - add, edit and delete players
    
    If a tournament is active, shows only participants of that tournament
    Otherwise shows full player management interface
    """
    # Check if there's an active tournament
    active_tournament_id = st.session_state.get('active_tournament_id')
    
    if active_tournament_id is not None:
        # Tournament is active - show only participants
        tournament = next((t for t in st.session_state.tournaments_list if t['id'] == active_tournament_id), None)
        
        if tournament and 'participants' in tournament and tournament['participants']:
            # Get participants DataFrame
            participants_ids = tournament['participants']
            participants_df = st.session_state.players_df[st.session_state.players_df['id'].isin(participants_ids)]
            
            # Display tournament participants table (non-editable)
            st.subheader(f"Tournament Participants ({len(participants_df)} players)")
            st.dataframe(
                participants_df[['name', 'wins', 'losses', 'points_difference', 'rating']],
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
                    ),
                },
                hide_index=True,
            )
            
            # Show how many players can be added based on the tournament limit
            if 'players_limit' in tournament:
                limit = tournament.get('players_limit', 0)
                if limit > 0:
                    remaining = max(0, limit - len(participants_ids))
                    if remaining > 0:
                        st.info(f"Tournament limit: {limit} players. You can add {remaining} more players.")
                    else:
                        st.warning(f"Tournament player limit ({limit}) reached. Cannot add more players.")
        else:
            st.warning("No participants added to this tournament yet.")
            # Изменяем переменную, чтобы переключиться на вкладку Tournament (tab3)
            if st.button("Add Players", key="btn_add_players"):
                st.session_state.active_tab = 2  # Индекс вкладки Tournament
                st.rerun()
        
        return
    
    # No active tournament - show full player management interface
    edited_df = st.data_editor(
        st.session_state.players_df[['name', 'email', 'phone', 'wins', 'losses', 'points_difference', 'rating']],
        num_rows="dynamic", 
        use_container_width=True,
        column_config={
            "name": "Player Name",
            "email": "Email",
            "phone": "Phone",
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
            
            # Проверяем наличие колонки 'id' и генерируем новые ID
            if 'id' not in st.session_state.players_df.columns:
                # Если колонки id еще нет, создаем её и начинаем с 1
                st.session_state.players_df['id'] = list(range(1, st.session_state.players_df.shape[0] + 1))
                new_ids = list(range(st.session_state.players_df.shape[0] + 1, 
                                    st.session_state.players_df.shape[0] + 1 + num_new_players))
            else:
                # Если колонка id существует, продолжаем с максимального значения
                new_ids = list(range(st.session_state.players_df['id'].max() + 1, 
                                    st.session_state.players_df['id'].max() + 1 + num_new_players))
            
            new_players = pd.DataFrame({
                'id': new_ids,
                'name': edited_df.iloc[-num_new_players:]['name'].values,
                'email': edited_df.iloc[-num_new_players:]['email'].values if 'email' in edited_df.columns else [""] * num_new_players,
                'phone': edited_df.iloc[-num_new_players:]['phone'].values if 'phone' in edited_df.columns else [""] * num_new_players,
                'wins': [0] * num_new_players,
                'losses': [0] * num_new_players,
                'points_won': [0] * num_new_players,
                'points_lost': [0] * num_new_players,
                'points_difference': [0] * num_new_players,
                'rating': [0] * num_new_players,
                'created_at': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] * num_new_players,
                'last_played': [""] * num_new_players
            })
            
            # Инициализируем историю рейтинга для новых игроков
            if 'rating_history' not in st.session_state:
                st.session_state.rating_history = {}
                
            # Получаем текущее время для записи в историю
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
            
            # Сохраняем обновленные данные
            storage.save_players_data()
        else:
            # Players removed
            # Find names that were in the original but not in the edited
            original_names = set(st.session_state.players_df['name'])
            edited_names = set(edited_df['name'])
            removed_names = original_names - edited_names
            
            # Remove those players
            st.session_state.players_df = st.session_state.players_df[~st.session_state.players_df['name'].isin(removed_names)]
            
            # Сохраняем обновленные данные
            storage.save_players_data()
            
    # Update player information
    st.session_state.players_df['name'] = edited_df['name'].values
    st.session_state.players_df['email'] = edited_df['email'].values
    st.session_state.players_df['phone'] = edited_df['phone'].values
    
    # Recalculate ratings after changes
    calculate_ratings()
    
    # Сохраняем данные игроков
    storage.save_players_data()

def calculate_ratings():
    """
    Calculate player ratings based on wins, losses and point differences
    """
    if len(st.session_state.players_df) > 0:
        # Проверяем и инициализируем все необходимые колонки
        for col in ['wins', 'losses', 'points_won', 'points_lost', 'points_difference']:
            if col not in st.session_state.players_df.columns:
                st.session_state.players_df[col] = 0
        
        # Проверяем, нужно ли вычислить points_difference
        if 'points_difference' not in st.session_state.players_df.columns:
            st.session_state.players_df['points_difference'] = st.session_state.players_df['points_won'] - st.session_state.players_df['points_lost']
        
        # Сохраняем предыдущие рейтинги для отслеживания изменений
        old_ratings = {}
        if 'rating' in st.session_state.players_df.columns:
            for _, row in st.session_state.players_df.iterrows():
                if 'id' in row and 'rating' in row:
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
    Display player statistics sorted by rating with player management interface
    """
    # Создаем вкладки для различных разделов
    stats_tab, manage_tab, test_tab = st.tabs(["Player Statistics", "Player Management", "Test Data"])
    
    with test_tab:
        st.subheader("Generate Test Players")
        col1, col2 = st.columns([3, 1])
        
        with col1:
            test_players_count = st.slider("Number of test players to generate:", 1, 30, 15)
        
        with col2:
            if st.button("Generate Players", use_container_width=True):
                num_added = generate_test_players(test_players_count)
                st.success(f"✅ Added {num_added} test players successfully!")
                st.rerun()
    
    with manage_tab:
        # Переносим интерфейс управления игроками сюда из Courts & Timer
        st.subheader("Manage Players")
        
        # Check if there's an active tournament
        active_tournament_id = st.session_state.get('active_tournament_id')
        
        if active_tournament_id is not None:
            # Tournament is active - show only participants
            tournament = next((t for t in st.session_state.tournaments_list if t['id'] == active_tournament_id), None)
            
            if tournament and 'participants' in tournament and tournament['participants']:
                # Get participants DataFrame
                participants_ids = tournament['participants']
                participants_df = st.session_state.players_df[st.session_state.players_df['id'].isin(participants_ids)]
                
                # Display tournament participants table (non-editable)
                st.subheader(f"Tournament Participants ({len(participants_df)} players)")
                st.dataframe(
                    participants_df[['name', 'wins', 'losses', 'points_difference', 'rating']],
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
                        ),
                    },
                    hide_index=True,
                )
                
                # Show how many players can be added based on the tournament limit
                if 'players_limit' in tournament:
                    limit = tournament.get('players_limit', 0)
                    if limit > 0:
                        remaining = max(0, limit - len(participants_ids))
                        if remaining > 0:
                            st.info(f"Tournament limit: {limit} players. You can add {remaining} more players.")
                        else:
                            st.warning(f"Tournament player limit ({limit}) reached. Cannot add more players.")
            else:
                st.warning("No participants added to this tournament yet.")
                # Изменяем переменную, чтобы переключиться на вкладку Tournament (tab3)
                if st.button("Add Players", key="btn_add_players"):
                    st.session_state.active_tab = 2  # Индекс вкладки Tournament
                    st.rerun()
        else:
            # No active tournament - show full player management interface
            
            # Проверяем наличие необходимых столбцов и создаем их при необходимости
            required_columns = ['name', 'email', 'phone', 'wins', 'losses', 'points_difference', 'rating']
            existing_columns = st.session_state.players_df.columns.tolist()
            
            # Создаем копию DataFrame для избежания ошибок при изменении
            df_for_editing = st.session_state.players_df.copy()
            
            # Добавляем недостающие столбцы
            for col in required_columns:
                if col not in existing_columns:
                    if col in ['wins', 'losses', 'points_difference', 'rating']:
                        df_for_editing[col] = 0
                    else:
                        df_for_editing[col] = ""
            
            # Теперь используем DataFrame с добавленными столбцами
            edited_df = st.data_editor(
                df_for_editing[required_columns],
                num_rows="dynamic", 
                use_container_width=True,
                column_config={
                    "name": "Player Name",
                    "email": "Email",
                    "phone": "Phone",
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
                    
                    # Проверяем наличие колонки 'id' и генерируем новые ID
                    if 'id' not in st.session_state.players_df.columns:
                        # Если колонки id еще нет, создаем её и начинаем с 1
                        st.session_state.players_df['id'] = list(range(1, st.session_state.players_df.shape[0] + 1))
                        new_ids = list(range(st.session_state.players_df.shape[0] + 1, 
                                            st.session_state.players_df.shape[0] + 1 + num_new_players))
                    else:
                        # Если колонка id существует, продолжаем с максимального значения
                        new_ids = list(range(st.session_state.players_df['id'].max() + 1, 
                                            st.session_state.players_df['id'].max() + 1 + num_new_players))
                    
                    new_players = pd.DataFrame({
                        'id': new_ids,
                        'name': edited_df.iloc[-num_new_players:]['name'].values,
                        'email': edited_df.iloc[-num_new_players:]['email'].values if 'email' in edited_df.columns else [""] * num_new_players,
                        'phone': edited_df.iloc[-num_new_players:]['phone'].values if 'phone' in edited_df.columns else [""] * num_new_players,
                        'wins': [0] * num_new_players,
                        'losses': [0] * num_new_players,
                        'points_won': [0] * num_new_players,
                        'points_lost': [0] * num_new_players,
                        'points_difference': [0] * num_new_players,
                        'rating': [0] * num_new_players,
                        'created_at': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] * num_new_players,
                        'last_played': [""] * num_new_players
                    })
                    
                    # Инициализируем историю рейтинга для новых игроков
                    if 'rating_history' not in st.session_state:
                        st.session_state.rating_history = {}
                        
                    # Получаем текущее время для записи в историю
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
                    
                    # Сохраняем обновленные данные
                    storage.save_players_data()
                else:
                    # Players removed
                    # Find names that were in the original but not in the edited
                    original_names = set(st.session_state.players_df['name'])
                    edited_names = set(edited_df['name'])
                    removed_names = original_names - edited_names
                    
                    # Remove those players
                    st.session_state.players_df = st.session_state.players_df[~st.session_state.players_df['name'].isin(removed_names)]
                    
                    # Сохраняем обновленные данные
                    storage.save_players_data()
                    
            # Update player information
            st.session_state.players_df['name'] = edited_df['name'].values
            st.session_state.players_df['email'] = edited_df['email'].values
            st.session_state.players_df['phone'] = edited_df['phone'].values
            
            # Recalculate ratings after changes
            calculate_ratings()
            
            # Сохраняем данные игроков
            storage.save_players_data()
    
    with stats_tab:
        # Проверяем, есть ли колонка 'rating'
        if 'rating' not in st.session_state.players_df.columns:
            # Вызываем пересчет рейтингов
            calculate_ratings()
        
        # Если players_df пуст или все равно нет рейтинга, добавляем колонку с нулями
        if 'rating' not in st.session_state.players_df.columns:
            st.session_state.players_df['rating'] = 0.0
        
        # Проверяем наличие нужных колонок и добавляем их, если они отсутствуют
        required_columns = ['name', 'wins', 'losses', 'points_won', 'points_lost', 'points_difference', 'rating', 'email', 'phone']
        for col in required_columns:
            if col not in st.session_state.players_df.columns:
                st.session_state.players_df[col] = 0 if col not in ['name', 'email', 'phone'] else ''
        
        # Копируем датафрейм перед сортировкой
        sorted_df = st.session_state.players_df.copy()
        
        # Вычисляем разницу очков если она не вычислена
        if 'points_difference' in sorted_df.columns:
            # Проверяем, есть ли нулевые значения в points_difference при ненулевых points_won/points_lost
            mask = (sorted_df['points_difference'] == 0) & ((sorted_df['points_won'] > 0) | (sorted_df['points_lost'] > 0))
            if mask.any():
                sorted_df.loc[mask, 'points_difference'] = sorted_df.loc[mask, 'points_won'] - sorted_df.loc[mask, 'points_lost']
        
        # Сортируем по рейтингу
        sorted_df = sorted_df.sort_values(by='rating', ascending=False).reset_index(drop=True)
        
        # Add rank column
        sorted_df.insert(0, 'rank', range(1, len(sorted_df) + 1))
        
        # Добавляем колонку для отображения стилизации
        sorted_df['status'] = ''
        
        # Добавляем стилизацию текста
        def highlight_winners_losers(df):
            styles = []
            for _, row in df.iterrows():
                if row['wins'] > row['losses']:
                    # Победитель - красным
                    styles.append('color: red; font-weight: bold')
                elif row['losses'] > row['wins']:
                    # Проигравший - синим
                    styles.append('color: blue')
                else:
                    # Нейтральный - стандартный
                    styles.append('')
            return styles
        
        # Create tabs for different views inside the stats tab
        perf_tab, contact_tab = st.tabs(["Performance Statistics", "Player Contact Information"])
        
        with perf_tab:
            # Проверяем, есть ли записи в таблице
            if len(sorted_df) == 0:
                st.info("Нет данных о игроках. Используйте вкладку 'Player Management' для добавления игроков.")
            else:
                # Преобразуем статус для лучшего отображения
                sorted_df.loc[sorted_df['wins'] > sorted_df['losses'], 'status'] = '🏆 Победитель'
                sorted_df.loc[sorted_df['losses'] > sorted_df['wins'], 'status'] = '⚠️ Проигравший'
                
                # Display the sorted performance stats with styling
                st.dataframe(
                    sorted_df[['rank', 'name', 'wins', 'losses', 'points_difference', 'rating', 'status']],
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
                        "status": "Status",
                    },
                    hide_index=True,
                )
        
        with contact_tab:
            # Проверяем, есть ли записи в таблице
            if len(sorted_df) == 0:
                st.info("Нет данных о игроках. Используйте вкладку 'Player Management' для добавления игроков.")
            else:
                # Display player contact information
                st.dataframe(
                    sorted_df[['rank', 'name', 'email', 'phone', 'rating', 'status']],
                    use_container_width=True,
                    column_config={
                        "rank": "Rank",
                        "name": "Player Name",
                        "email": "Email",
                        "phone": "Phone",
                        "rating": st.column_config.NumberColumn(
                            "Rating",
                            help="Player rating based on performance",
                            format="%.2f",
                        ),
                        "status": "Status",
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
    
    # Проверяем, существует ли колонка points_difference
    if 'points_difference' not in st.session_state.players_df.columns:
        st.session_state.players_df['points_difference'] = st.session_state.players_df['points_won'] - st.session_state.players_df['points_lost']
    
    # Проверяем наличие колонок points_won и points_lost
    for col in ['points_won', 'points_lost']:
        if col not in st.session_state.players_df.columns:
            st.session_state.players_df[col] = 0
    
    # Update stats for team A
    for player_id in team_a_ids:
        player_idx = st.session_state.players_df.loc[st.session_state.players_df['id'] == player_id].index[0]
        
        if team_a_score > team_b_score:
            st.session_state.players_df.at[player_idx, 'wins'] += 1
        else:
            st.session_state.players_df.at[player_idx, 'losses'] += 1
        
        # Обновляем количество набранных и пропущенных очков
        st.session_state.players_df.at[player_idx, 'points_won'] += team_a_score
        st.session_state.players_df.at[player_idx, 'points_lost'] += team_b_score
        
        # Обновляем разницу очков
        st.session_state.players_df.at[player_idx, 'points_difference'] = (
            st.session_state.players_df.at[player_idx, 'points_won'] - 
            st.session_state.players_df.at[player_idx, 'points_lost']
        )
        
        # Обновляем дату последней игры
        st.session_state.players_df.at[player_idx, 'last_played'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Update stats for team B
    for player_id in team_b_ids:
        player_idx = st.session_state.players_df.loc[st.session_state.players_df['id'] == player_id].index[0]
        
        if team_b_score > team_a_score:
            st.session_state.players_df.at[player_idx, 'wins'] += 1
        else:
            st.session_state.players_df.at[player_idx, 'losses'] += 1
        
        # Обновляем количество набранных и пропущенных очков
        st.session_state.players_df.at[player_idx, 'points_won'] += team_b_score
        st.session_state.players_df.at[player_idx, 'points_lost'] += team_a_score
        
        # Обновляем разницу очков
        st.session_state.players_df.at[player_idx, 'points_difference'] = (
            st.session_state.players_df.at[player_idx, 'points_won'] - 
            st.session_state.players_df.at[player_idx, 'points_lost']
        )
        
        # Обновляем дату последней игры
        st.session_state.players_df.at[player_idx, 'last_played'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Сохраняем историю игры
    save_game_history(court_idx, court, team_a_score, team_b_score)
    
    # Recalculate ratings
    calculate_ratings()
    
    # Сохраняем обновленные данные игроков и историю игр
    storage.save_players_data()
    storage.save_game_history()

def generate_test_players(num_players=15):
    """
    Генерирует случайных тестовых игроков с начальными характеристиками
    
    Parameters:
    - num_players: Количество игроков для генерации
    """
    # Проверяем, есть ли структура players_df
    if 'players_df' not in st.session_state or st.session_state.players_df is None:
        # Создаем DataFrame если его нет
        st.session_state.players_df = pd.DataFrame(columns=[
            'id', 'name', 'email', 'phone', 'wins', 'losses', 
            'points_won', 'points_lost', 'points_difference', 'rating',
            'created_at', 'last_played'
        ])
    
    # Проверяем наличие колонки 'id' и определяем начальный ID
    next_id = 1
    if 'id' in st.session_state.players_df.columns and not st.session_state.players_df.empty:
        next_id = st.session_state.players_df['id'].max() + 1 if not st.session_state.players_df.empty else 1
    
    # Создаем имена
    first_names = ["Alex", "David", "Elena", "Sophia", "Michael", "Julia", "Ivan", "Anna", "Pavel", 
                  "Natalia", "Victor", "Marina", "Sergey", "Olga", "Andrey", "Tatiana", "Nikolay", "Irina"]
    last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", 
                 "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin"]
    
    # Генерируем случайных игроков
    new_players = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for i in range(num_players):
        player_id = next_id + i
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        
        # Случайное количество игр для каждого игрока (0-5)
        num_games = random.randint(0, 5)
        wins = random.randint(0, num_games)
        losses = num_games - wins
        
        # Случайное количество очков
        points_won = random.randint(0, 50)
        points_lost = random.randint(0, 40)
        points_difference = points_won - points_lost
        
        # Рассчитываем начальный рейтинг
        rating = (wins - losses) + (points_difference / 100)
        
        # Создаем email и телефон
        email = f"{name.lower().replace(' ', '.')}@example.com"
        phone = f"+7{random.randint(9000000000, 9999999999)}"
        
        # Записываем в лист нового игрока
        new_players.append({
            'id': player_id,
            'name': name,
            'email': email,
            'phone': phone,
            'wins': wins,
            'losses': losses,
            'points_won': points_won,
            'points_lost': points_lost,
            'points_difference': points_difference,
            'rating': rating,
            'created_at': timestamp,
            'last_played': timestamp if num_games > 0 else ""
        })
        
        # Инициализируем историю рейтинга
        if 'rating_history' not in st.session_state:
            st.session_state.rating_history = {}
            
        if player_id not in st.session_state.rating_history:
            st.session_state.rating_history[player_id] = []
            
        st.session_state.rating_history[player_id].append({
            'timestamp': timestamp,
            'rating': rating
        })
    
    # Добавляем новых игроков в DataFrame
    new_players_df = pd.DataFrame(new_players)
    st.session_state.players_df = pd.concat([st.session_state.players_df, new_players_df], ignore_index=True)
    
    # Сохраняем обновленные данные
    storage.save_players_data()
    
    return len(new_players)

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
    # Уже импортировано в начале файла
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
