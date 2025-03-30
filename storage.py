import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# Константы для файлов хранения
PLAYERS_DATA_FILE = 'players_data.json'
GAME_HISTORY_FILE = 'game_history.json'
TOURNAMENTS_DATA_FILE = 'tournaments_data.json'

def save_players_data():
    """
    Сохраняет данные игроков в JSON файл
    """
    if 'players_df' in st.session_state:
        # Преобразуем DataFrame в список словарей
        players_data = st.session_state.players_df.to_dict('records')
        
        # Обрабатываем datetime объекты для корректной сериализации
        for player in players_data:
            for key, value in player.items():
                if isinstance(value, datetime):
                    player[key] = value.isoformat()
        
        # Сохраняем в файл
        with open(PLAYERS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(players_data, f, ensure_ascii=False, indent=4)
        
        return True
    return False

def load_players_data():
    """
    Загружает данные игроков из JSON файла
    
    Returns:
        DataFrame с данными игроков или пустой DataFrame если файл не найден
    """
    if os.path.exists(PLAYERS_DATA_FILE):
        try:
            with open(PLAYERS_DATA_FILE, 'r', encoding='utf-8') as f:
                players_data = json.load(f)
            
            # Преобразуем список словарей в DataFrame
            df = pd.DataFrame(players_data)
            
            # Преобразуем строки в datetime объекты
            date_columns = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='ignore')
            
            return df
        except Exception as e:
            st.error(f"Ошибка при загрузке данных игроков: {e}")
            return pd.DataFrame()
    else:
        # Возвращаем пустой DataFrame с нужными колонками
        return pd.DataFrame(columns=[
            'id', 'name', 'phone', 'email', 'rating', 
            'wins', 'losses', 'points_won', 'points_lost', 'points_difference',
            'created_at', 'last_played'
        ])

def save_game_history():
    """
    Сохраняет историю игр в JSON файл
    """
    if 'game_history' in st.session_state:
        # Преобразуем datetime объекты для корректной сериализации
        game_history = []
        for game in st.session_state.game_history:
            game_copy = game.copy()
            for key, value in game_copy.items():
                if isinstance(value, datetime):
                    game_copy[key] = value.isoformat()
            game_history.append(game_copy)
        
        # Сохраняем в файл
        with open(GAME_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(game_history, f, ensure_ascii=False, indent=4)
        
        return True
    return False

def load_game_history():
    """
    Загружает историю игр из JSON файла
    
    Returns:
        Список с историей игр или пустой список если файл не найден
    """
    if os.path.exists(GAME_HISTORY_FILE):
        try:
            with open(GAME_HISTORY_FILE, 'r', encoding='utf-8') as f:
                game_history = json.load(f)
            
            # Преобразуем строки в datetime объекты
            for game in game_history:
                for key, value in game.items():
                    if key == 'timestamp' or 'date' in key.lower() or 'time' in key.lower():
                        try:
                            game[key] = datetime.fromisoformat(value)
                        except (ValueError, TypeError):
                            pass
            
            return game_history
        except Exception as e:
            st.error(f"Ошибка при загрузке истории игр: {e}")
            return []
    else:
        return []

def save_tournaments_data():
    """
    Сохраняет данные турниров в JSON файл
    """
    # Сохраняем tournaments_list, если он существует
    if 'tournaments_list' in st.session_state:
        # Преобразуем datetime объекты для корректной сериализации
        tournaments_list = []
        for tournament in st.session_state.tournaments_list:
            tournament_copy = tournament.copy()
            for key, value in tournament_copy.items():
                if isinstance(value, datetime):
                    tournament_copy[key] = value.isoformat()
            tournaments_list.append(tournament_copy)
        
        # Сохраняем в файл
        with open(TOURNAMENTS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(tournaments_list, f, ensure_ascii=False, indent=4)
        
        return True
    
    # Сохраняем tournaments, если он существует (для обратной совместимости)
    elif 'tournaments' in st.session_state:
        # Преобразуем datetime объекты для корректной сериализации
        tournaments_data = {}
        for tournament_id, tournament in st.session_state.tournaments.items():
            tournament_copy = tournament.copy()
            for key, value in tournament_copy.items():
                if isinstance(value, datetime):
                    tournament_copy[key] = value.isoformat()
            tournaments_data[tournament_id] = tournament_copy
        
        # Сохраняем в файл
        with open(TOURNAMENTS_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(tournaments_data, f, ensure_ascii=False, indent=4)
        
        return True
        
    return False

def load_tournaments_data():
    """
    Загружает данные турниров из JSON файла
    
    Returns:
        Словарь с данными турниров или пустой словарь если файл не найден
    """
    if os.path.exists(TOURNAMENTS_DATA_FILE):
        try:
            with open(TOURNAMENTS_DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Проверяем формат данных (список или словарь)
            if isinstance(data, list):
                # Формат списка - новая версия (tournaments_list)
                tournaments_list = data
                
                # Преобразуем строки в datetime объекты
                for tournament in tournaments_list:
                    for key, value in tournament.items():
                        if isinstance(value, str) and ('date' in key.lower() or 'time' in key.lower() or key == 'start_time' or key == 'end_time'):
                            try:
                                tournament[key] = datetime.fromisoformat(value)
                            except ValueError:
                                pass
                
                # Инициализируем st.session_state.tournaments_list
                st.session_state.tournaments_list = tournaments_list
                return {}  # Возвращаем пустой словарь для обратной совместимости
                
            else:
                # Формат словаря - старая версия
                tournaments_data = data
                
                # Преобразуем строки в datetime объекты
                for tournament_id, tournament in tournaments_data.items():
                    for key, value in tournament.items():
                        if isinstance(value, str) and ('date' in key.lower() or 'time' in key.lower() or key == 'start_time' or key == 'end_time'):
                            try:
                                tournament[key] = datetime.fromisoformat(value)
                            except ValueError:
                                pass
                
                return tournaments_data
                
        except Exception as e:
            st.error(f"Ошибка при загрузке данных турниров: {e}")
            return {}
    else:
        return {}

def initialize_storage():
    """
    Инициализирует хранилище данных при запуске приложения
    """
    # Инициализируем данные игроков
    if 'players_df' not in st.session_state:
        st.session_state.players_df = load_players_data()
        
        # Проверяем, есть ли колонка points_difference
        if 'points_difference' not in st.session_state.players_df.columns and len(st.session_state.players_df) > 0:
            # Если есть колонки points_won и points_lost, создаем points_difference
            if 'points_won' in st.session_state.players_df.columns and 'points_lost' in st.session_state.players_df.columns:
                st.session_state.players_df['points_difference'] = st.session_state.players_df['points_won'] - st.session_state.players_df['points_lost']
            else:
                # Иначе инициализируем нулями
                st.session_state.players_df['points_difference'] = 0
    
    # Инициализируем историю игр
    if 'game_history' not in st.session_state:
        st.session_state.game_history = load_game_history()
    
    # Инициализируем данные турниров
    if 'tournaments' not in st.session_state:
        st.session_state.tournaments = load_tournaments_data()
    
    # Проверяем, не загрузились ли tournaments_list уже из файла в load_tournaments_data
    if 'tournaments_list' not in st.session_state:
        # Если не загрузились, создаем пустой список
        st.session_state.tournaments_list = []

def auto_save_data():
    """
    Автоматически сохраняет все данные
    Может быть вызвана периодически или при изменении данных
    """
    save_players_data()
    save_game_history()
    save_tournaments_data()