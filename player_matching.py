import streamlit as st
import pandas as pd
import numpy as np
import random
from itertools import combinations

def get_skill_based_courts(players_df):
    """
    Создает распределение игроков по кортам на основе их рейтинга/навыков
    
    Parameters:
    - players_df: DataFrame с информацией об игроках, включая их рейтинг
    
    Returns:
    - List of courts with optimized player allocations
    """
    if len(players_df) < 4:
        st.warning("Для создания корта требуется минимум 4 игрока")
        return []
    
    # Получаем копию DataFrame с игроками, отсортированными по рейтингу
    sorted_players = players_df.sort_values(by='rating', ascending=False).copy()
    
    # Получаем ID игроков, отсортированных по рейтингу
    player_ids = sorted_players['id'].tolist()
    
    # Определяем количество кортов и необходимость отдыхающего корта
    num_players = len(player_ids)
    num_full_courts = num_players // 4
    has_rest_court = num_players % 4 != 0
    
    # Инициализируем список кортов
    courts = []
    
    # Используем алгоритм "змейки" для равномерного распределения игроков по уровню
    # Это гарантирует, что сильные игроки будут распределены по разным кортам
    distributed_players = snake_algorithm(player_ids, num_full_courts)
    
    # Распределяем игроков по кортам
    for i in range(num_full_courts):
        court_players = distributed_players[i]
        
        # Создаем команды с максимально близкими суммарными рейтингами
        team_a, team_b = create_balanced_teams(court_players, sorted_players)
        
        court = {
            'court_number': i + 1,
            'team_a': team_a,
            'team_b': team_b,
            'is_rest': False
        }
        courts.append(court)
    
    # Создаем корт для отдыхающих игроков, если необходимо
    if has_rest_court:
        rest_players = player_ids[num_full_courts * 4:]
        court = {
            'court_number': num_full_courts + 1,
            'team_a': rest_players,
            'team_b': [],
            'is_rest': True
        }
        courts.append(court)
    
    return courts

def snake_algorithm(player_ids, num_courts):
    """
    Реализует алгоритм "змейки" для распределения игроков по кортам
    Порядок распределения: 
    Корт 1, Корт 2, ..., Корт N, Корт N, ..., Корт 2, Корт 1, Корт 1, ...
    
    Parameters:
    - player_ids: Список ID игроков, отсортированных по рейтингу (от высокого к низкому)
    - num_courts: Количество кортов
    
    Returns:
    - Список списков ID игроков для каждого корта
    """
    if num_courts == 0:
        return []
    
    # Инициализируем пустые списки для каждого корта
    court_players = [[] for _ in range(num_courts)]
    
    # Определяем количество игроков для полных кортов (по 4 на корт)
    num_players_for_courts = num_courts * 4
    
    # Обрезаем список игроков до необходимого количества
    players_to_distribute = player_ids[:num_players_for_courts]
    
    # Распределяем игроков "змейкой"
    direction = 1  # 1 - вперед, -1 - назад
    court_idx = 0
    
    for i, player_id in enumerate(players_to_distribute):
        court_players[court_idx].append(player_id)
        
        # Изменяем направление, если достигли края
        if court_idx == 0 and direction == -1:
            direction = 1
        elif court_idx == num_courts - 1 and direction == 1:
            direction = -1
        else:
            court_idx += direction
    
    return court_players

def create_balanced_teams(court_players, players_df):
    """
    Создает максимально сбалансированные команды внутри корта
    
    Parameters:
    - court_players: Список из 4 ID игроков для одного корта
    - players_df: DataFrame с информацией о игроках
    
    Returns:
    - team_a: Список ID игроков для команды A
    - team_b: Список ID игроков для команды B
    """
    # Получаем рейтинги игроков
    player_ratings = {player_id: players_df.loc[players_df['id'] == player_id, 'rating'].values[0] 
                      for player_id in court_players}
    
    # Генерируем все возможные комбинации для команды А (2 игрока из 4)
    possible_teams = list(combinations(court_players, 2))
    
    # Находим комбинацию с минимальной разницей суммарного рейтинга
    min_diff = float('inf')
    best_team_a = None
    best_team_b = None
    
    for team_a_combo in possible_teams:
        team_a_rating = sum(player_ratings[player_id] for player_id in team_a_combo)
        team_b_combo = tuple(player_id for player_id in court_players if player_id not in team_a_combo)
        team_b_rating = sum(player_ratings[player_id] for player_id in team_b_combo)
        
        diff = abs(team_a_rating - team_b_rating)
        
        if diff < min_diff:
            min_diff = diff
            best_team_a = list(team_a_combo)
            best_team_b = list(team_b_combo)
    
    # Если не удалось найти комбинацию, используем стандартное разделение
    if best_team_a is None or best_team_b is None:
        best_team_a = court_players[:2]
        best_team_b = court_players[2:]
    
    return best_team_a, best_team_b

def get_optimized_rotation(current_courts, players_df):
    """
    Создает оптимальную ротацию игроков между кортами, учитывая их навыки
    
    Parameters:
    - current_courts: Текущее распределение кортов
    - players_df: DataFrame с информацией о игроках
    
    Returns:
    - Новый список кортов с оптимизированным распределением игроков
    """
    # Собираем всех игроков из существующих кортов
    all_players = []
    for court in current_courts:
        all_players.extend(court['team_a'])
        all_players.extend(court['team_b'])
    
    # Используем алгоритм расположения по навыкам для создания новых кортов
    return get_skill_based_courts(players_df[players_df['id'].isin(all_players)])

def display_matchmaking_settings():
    """
    Отображает настройки для алгоритма подбора игроков
    """
    st.subheader("Настройки алгоритма подбора игроков")
    
    # Выбор стратегии подбора игроков
    strategy = st.radio(
        "Выберите стратегию распределения игроков:",
        ["Случайное распределение", "Сбалансированные команды по навыкам"]
    )
    
    return strategy

def calculate_court_balance(court, players_df):
    """
    Рассчитывает дисбаланс команд на корте (разницу в суммарном рейтинге)
    
    Parameters:
    - court: Словарь с информацией о корте
    - players_df: DataFrame с информацией о игроках
    
    Returns:
    - Разница в суммарном рейтинге между командами
    """
    if court['is_rest'] or not court['team_a'] or not court['team_b']:
        return 0
    
    # Получаем рейтинги игроков
    team_a_rating = sum(players_df.loc[players_df['id'] == player_id, 'rating'].values[0] 
                        for player_id in court['team_a'])
    team_b_rating = sum(players_df.loc[players_df['id'] == player_id, 'rating'].values[0] 
                        for player_id in court['team_b'])
    
    return abs(team_a_rating - team_b_rating)