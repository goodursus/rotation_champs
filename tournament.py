import streamlit as st
import pandas as pd
import numpy as np
import math
import time
from datetime import datetime

def create_tournament(players_df):
    """
    Создает новый турнир с сеткой на основе списка игроков
    
    Parameters:
    - players_df: DataFrame с информацией об игроках
    
    Returns:
    - tournament_data: словарь с данными турнира
    """
    if 'tournament_data' not in st.session_state:
        st.session_state.tournament_data = {
            'created_at': datetime.now(),
            'status': 'setup',  # setup, active, completed
            'name': '',
            'bracket_type': 'single',  # single, double
            'rounds': [],
            'current_round': 0,
            'matches': [],
            'player_ids': [],
            'winners': [],
            'runner_ups': []
        }
    
    return st.session_state.tournament_data

def generate_bracket(tournament_data, player_ids):
    """
    Генерирует турнирную сетку на основе списка игроков
    
    Parameters:
    - tournament_data: словарь с данными турнира
    - player_ids: список ID игроков-участников
    
    Returns:
    - обновленные данные турнира
    """
    # Очищаем предыдущие данные
    tournament_data['rounds'] = []
    tournament_data['matches'] = []
    tournament_data['current_round'] = 0
    tournament_data['player_ids'] = player_ids
    
    # Определяем количество игроков и раундов
    num_players = len(player_ids)
    num_rounds = math.ceil(math.log2(num_players))
    
    # Определяем количество "пустых" слотов (byes)
    total_slots = 2 ** num_rounds
    num_byes = total_slots - num_players
    
    # Перемешиваем игроков для случайной сетки
    shuffled_players = player_ids.copy()
    np.random.shuffle(shuffled_players)
    
    # Создаем список всех позиций сетки, включая пустые
    positions = [None] * total_slots
    
    # Заполняем позиции игроками
    for i in range(num_players):
        positions[i] = shuffled_players[i]
    
    # Создаем матчи первого раунда
    matches = []
    for i in range(0, total_slots, 2):
        player1 = positions[i]
        player2 = positions[i + 1]
        
        match = {
            'id': len(matches) + 1,
            'round': 0,
            'player1': player1,
            'player2': player2,
            'winner': None,
            'score': {'player1': 0, 'player2': 0},
            'status': 'pending'  # pending, active, completed
        }
        
        # Если один из игроков отсутствует (bye), сразу отмечаем победителя
        if player1 is None and player2 is not None:
            match['winner'] = player2
            match['status'] = 'completed'
        elif player2 is None and player1 is not None:
            match['winner'] = player1
            match['status'] = 'completed'
            
        matches.append(match)
    
    tournament_data['matches'] = matches
    
    # Создаем структуру раундов
    rounds = []
    remaining_matches = total_slots // 2
    for r in range(num_rounds):
        round_data = {
            'round_number': r,
            'name': f"Round {r+1}" if r < num_rounds - 1 else "Final",
            'matches': list(range(len(matches) - remaining_matches, len(matches))),
            'status': 'pending'  # pending, active, completed
        }
        rounds.append(round_data)
        remaining_matches //= 2
        
        # Добавляем пустые матчи для следующих раундов
        if r < num_rounds - 1:
            for i in range(remaining_matches):
                match = {
                    'id': len(matches) + 1,
                    'round': r + 1,
                    'player1': None,
                    'player2': None,
                    'winner': None,
                    'score': {'player1': 0, 'player2': 0},
                    'status': 'pending'
                }
                matches.append(match)
    
    # Обновляем данные турнира
    tournament_data['rounds'] = rounds
    tournament_data['matches'] = matches
    
    # Устанавливаем первый раунд как активный
    if len(rounds) > 0:
        rounds[0]['status'] = 'active'
        tournament_data['current_round'] = 0
        
        # Устанавливаем первые матчи как активные
        for match_idx in rounds[0]['matches']:
            # Пропускаем матчи с автоматическими победителями (bye)
            if tournament_data['matches'][match_idx]['status'] != 'completed':
                tournament_data['matches'][match_idx]['status'] = 'active'
    
    return tournament_data

def display_tournament_setup():
    """
    Отображает интерфейс настройки турнира
    """
    st.header("Настройка турнира")
    
    # Создаем или получаем данные турнира
    tournament_data = create_tournament(st.session_state.players_df)
    
    # Настройки турнира
    col1, col2 = st.columns(2)
    
    with col1:
        tournament_name = st.text_input("Название турнира", 
                                       value=tournament_data.get('name', ''),
                                       placeholder="Введите название турнира")
        
        if tournament_name:
            tournament_data['name'] = tournament_name
    
    with col2:
        bracket_type = st.selectbox(
            "Тип турнирной сетки",
            options=["Одиночная сетка", "Двойная сетка"],
            index=0 if tournament_data.get('bracket_type', 'single') == 'single' else 1
        )
        
        if bracket_type == "Одиночная сетка":
            tournament_data['bracket_type'] = 'single'
        else:
            tournament_data['bracket_type'] = 'double'
    
    # Выбор игроков для турнира
    st.subheader("Выберите участников турнира")
    
    # Показываем список всех игроков с возможностью выбора
    if not st.session_state.players_df.empty:
        # Создаем список для отслеживания выбранных игроков
        selected_players = []
        
        # Отображаем игроков в виде таблицы с чекбоксами
        for index, player in st.session_state.players_df.iterrows():
            col1, col2 = st.columns([1, 5])
            with col1:
                selected = st.checkbox("", 
                                     value=player['id'] in tournament_data.get('player_ids', []),
                                     key=f"player_{player['id']}")
            with col2:
                st.write(f"{player['name']} (Рейтинг: {player['rating']:.2f})")
            
            if selected:
                selected_players.append(player['id'])
        
        tournament_data['player_ids'] = selected_players
        
        # Отображаем количество выбранных игроков
        st.write(f"Выбрано игроков: {len(selected_players)}")
        
        # Проверка минимального количества игроков для турнира
        min_players = 4
        if len(selected_players) < min_players:
            st.warning(f"Для создания турнира необходимо выбрать не менее {min_players} игроков.")
            can_start = False
        else:
            can_start = True
            
        # Кнопка для генерации турнирной сетки
        if can_start:
            if st.button("Создать турнирную сетку"):
                tournament_data = generate_bracket(tournament_data, selected_players)
                tournament_data['status'] = 'active'
                st.session_state.tournament_data = tournament_data
                st.success("Турнирная сетка успешно создана!")
                st.rerun()
    else:
        st.info("Добавьте игроков, чтобы создать турнир")

def advance_match(match_id, player1_score, player2_score):
    """
    Записывает результат матча и продвигает победителя в следующий раунд
    
    Parameters:
    - match_id: ID матча
    - player1_score: счет первого игрока
    - player2_score: счет второго игрока
    """
    tournament_data = st.session_state.tournament_data
    match = next((m for m in tournament_data['matches'] if m['id'] == match_id), None)
    
    if not match:
        return
    
    # Обновляем счет
    match['score']['player1'] = player1_score
    match['score']['player2'] = player2_score
    
    # Определяем победителя
    if player1_score > player2_score:
        match['winner'] = match['player1']
    else:
        match['winner'] = match['player2']
    
    # Отмечаем матч как завершенный
    match['status'] = 'completed'
    
    # Проверяем текущий раунд
    current_round = tournament_data['rounds'][tournament_data['current_round']]
    
    # Находим следующий матч для победителя
    if tournament_data['current_round'] < len(tournament_data['rounds']) - 1:
        # Индекс текущего матча в раунде
        match_index = current_round['matches'].index(match_id - 1)
        
        # Индекс следующего матча
        next_round = tournament_data['rounds'][tournament_data['current_round'] + 1]
        next_match_index = match_index // 2
        
        if next_match_index < len(next_round['matches']):
            next_match_id = next_round['matches'][next_match_index]
            next_match = tournament_data['matches'][next_match_id]
            
            # Определяем, какой слот заполнить
            if match_index % 2 == 0:
                next_match['player1'] = match['winner']
            else:
                next_match['player2'] = match['winner']
            
            # Если оба игрока определены, активируем матч
            if next_match['player1'] is not None and next_match['player2'] is not None:
                next_match['status'] = 'active'
    
    # Проверяем, завершены ли все матчи в текущем раунде
    all_completed = True
    for match_idx in current_round['matches']:
        if tournament_data['matches'][match_idx]['status'] != 'completed':
            all_completed = False
            break
    
    # Если все матчи завершены, переходим к следующему раунду
    if all_completed:
        current_round['status'] = 'completed'
        
        # Если есть следующий раунд, активируем его
        if tournament_data['current_round'] < len(tournament_data['rounds']) - 1:
            tournament_data['current_round'] += 1
            tournament_data['rounds'][tournament_data['current_round']]['status'] = 'active'
        else:
            # Турнир завершен
            tournament_data['status'] = 'completed'
            
            # Определяем победителя и финалиста
            final_match = tournament_data['matches'][current_round['matches'][0]]
            tournament_data['winners'] = [final_match['winner']]
            
            # Определяем серебряного призера (runner-up)
            if final_match['player1'] == final_match['winner']:
                tournament_data['runner_ups'] = [final_match['player2']]
            else:
                tournament_data['runner_ups'] = [final_match['player1']]
    
    # Обновляем данные турнира в сессии
    st.session_state.tournament_data = tournament_data

def get_player_name(player_id):
    """
    Возвращает имя игрока по его ID
    
    Parameters:
    - player_id: ID игрока
    
    Returns:
    - имя игрока или 'BYE' если ID None
    """
    if player_id is None:
        return 'BYE'
    
    player = st.session_state.players_df[st.session_state.players_df['id'] == player_id]
    if not player.empty:
        return player.iloc[0]['name']
    return f"Игрок {player_id}"

def display_tournament_bracket():
    """
    Отображает турнирную сетку и текущие матчи
    """
    tournament_data = st.session_state.tournament_data
    
    # Отображаем заголовок и информацию о турнире
    st.header(f"Турнир: {tournament_data.get('name', 'Без названия')}")
    
    # Отображаем статус турнира
    status_text = "Настройка"
    if tournament_data['status'] == 'active':
        status_text = "В процессе"
    elif tournament_data['status'] == 'completed':
        status_text = "Завершён"
    
    st.subheader(f"Статус: {status_text}")
    
    # Если турнир завершен, показываем победителей
    if tournament_data['status'] == 'completed':
        st.subheader("🏆 Победители")
        winner_id = tournament_data['winners'][0] if tournament_data['winners'] else None
        runner_up_id = tournament_data['runner_ups'][0] if tournament_data['runner_ups'] else None
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**🥇 1 место:** {get_player_name(winner_id)}")
        with col2:
            st.markdown(f"**🥈 2 место:** {get_player_name(runner_up_id)}")
    
    # Отображаем текущие матчи, если турнир активен
    if tournament_data['status'] == 'active':
        st.subheader("Текущие матчи")
        
        current_round = tournament_data['rounds'][tournament_data['current_round']]
        st.write(f"**{current_round['name']}**")
        
        # Показываем активные матчи текущего раунда
        active_matches = []
        for match_idx in current_round['matches']:
            match = tournament_data['matches'][match_idx]
            if match['status'] == 'active':
                active_matches.append(match)
        
        if active_matches:
            for match in active_matches:
                match_container = st.container()
                with match_container:
                    st.markdown(f"**Матч #{match['id']}**")
                    
                    col1, col2, col3 = st.columns([2, 1, 2])
                    
                    with col1:
                        player1_name = get_player_name(match['player1'])
                        st.markdown(f"**{player1_name}**")
                    
                    with col2:
                        st.markdown("vs")
                    
                    with col3:
                        player2_name = get_player_name(match['player2'])
                        st.markdown(f"**{player2_name}**")
                    
                    # Добавляем поля для ввода счета
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        player1_score = st.number_input(
                            f"Счет {player1_name}", 
                            min_value=0, 
                            value=match['score']['player1'],
                            key=f"score_p1_{match['id']}"
                        )
                    
                    with col2:
                        player2_score = st.number_input(
                            f"Счет {player2_name}", 
                            min_value=0, 
                            value=match['score']['player2'],
                            key=f"score_p2_{match['id']}"
                        )
                    
                    # Кнопка для завершения матча
                    if st.button("Завершить матч", key=f"finish_match_{match['id']}"):
                        advance_match(match['id'], player1_score, player2_score)
                        st.rerun()
        else:
            st.info("Нет активных матчей в текущем раунде.")
    
    # Отображаем полную турнирную сетку
    st.subheader("Турнирная сетка")
    
    # Определяем количество раундов для отображения
    num_rounds = len(tournament_data['rounds'])
    
    if num_rounds > 0:
        # Отображаем сетку по раундам
        cols = st.columns(num_rounds)
        
        for r, round_data in enumerate(tournament_data['rounds']):
            with cols[r]:
                st.markdown(f"**{round_data['name']}**")
                
                for match_idx in round_data['matches']:
                    match = tournament_data['matches'][match_idx]
                    
                    # Определяем стиль отображения в зависимости от статуса
                    if match['status'] == 'completed':
                        bg_color = "#e6f7e6"  # светло-зеленый для завершенных
                    elif match['status'] == 'active':
                        bg_color = "#ffeb99"  # светло-желтый для активных
                    else:
                        bg_color = "#f0f0f0"  # светло-серый для ожидающих
                    
                    # Имена игроков
                    player1_name = get_player_name(match['player1'])
                    player2_name = get_player_name(match['player2'])
                    
                    # Отображаем матч с стилем в зависимости от статуса
                    match_html = f"""
                    <div style="
                        background-color: {bg_color}; 
                        border-radius: 4px; 
                        padding: 8px; 
                        margin-bottom: 10px;
                        border: 1px solid #ddd;">
                        <div style="
                            display: flex; 
                            justify-content: space-between; 
                            margin-bottom: 5px;">
                            <span style="
                                font-weight: {'bold' if match['winner'] == match['player1'] else 'normal'};
                                text-decoration: {'line-through' if match['winner'] == match['player2'] else 'none'};
                                flex: 3;">
                                {player1_name}
                            </span>
                            <span style="flex: 1; text-align: right;">
                                {match['score']['player1']}
                            </span>
                        </div>
                        <div style="
                            display: flex; 
                            justify-content: space-between;">
                            <span style="
                                font-weight: {'bold' if match['winner'] == match['player2'] else 'normal'};
                                text-decoration: {'line-through' if match['winner'] == match['player1'] else 'none'};
                                flex: 3;">
                                {player2_name}
                            </span>
                            <span style="flex: 1; text-align: right;">
                                {match['score']['player2']}
                            </span>
                        </div>
                    </div>
                    """
                    st.markdown(match_html, unsafe_allow_html=True)
    else:
        st.info("Турнирная сетка пуста.")

def display_tournament():
    """
    Основная функция для отображения интерфейса турнира
    """
    if 'tournament_data' not in st.session_state or st.session_state.tournament_data['status'] == 'setup':
        display_tournament_setup()
    else:
        # Отображаем кнопку для начала нового турнира
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Новый турнир"):
                # Сбрасываем данные турнира
                st.session_state.tournament_data = {
                    'created_at': datetime.now(),
                    'status': 'setup',
                    'name': '',
                    'bracket_type': 'single',
                    'rounds': [],
                    'current_round': 0,
                    'matches': [],
                    'player_ids': [],
                    'winners': [],
                    'runner_ups': []
                }
                st.rerun()
        
        # Отображаем турнирную сетку
        display_tournament_bracket()