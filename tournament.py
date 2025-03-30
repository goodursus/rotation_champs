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
            'runner_ups': [],
            'duration_minutes': 120,  # Длительность турнира (2 часа по умолчанию)
            'game_duration_minutes': 15,  # Длительность одной игры
            'players_limit': 0,  # Ограничение на количество игроков (0 = без ограничений)
            'participants': []  # Список ID игроков-участников (используется после создания турнира)
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
    
    # Добавляем настройки времени и ограничения по игрокам
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Продолжительность турнира
        tournament_duration = st.number_input(
            "Продолжительность турнира (мин)", 
            min_value=5,  # Снижено с 30 до 5 минут для тестирования
            max_value=480, 
            value=tournament_data.get('duration_minutes', 120),
            step=5
        )
        tournament_data['duration_minutes'] = tournament_duration
    
    with col2:
        # Продолжительность одной игры
        game_duration = st.number_input(
            "Продолжительность игры (мин)", 
            min_value=1,  # Снижено с 5 до 1 минуты для тестирования
            max_value=60, 
            value=tournament_data.get('game_duration_minutes', 15),
            step=1
        )
        tournament_data['game_duration_minutes'] = game_duration
    
    with col3:
        # Ограничение по количеству игроков
        players_limit = st.number_input(
            "Лимит игроков (0 = без ограничений)", 
            min_value=0, 
            max_value=100, 
            value=tournament_data.get('players_limit', 0)
        )
        tournament_data['players_limit'] = players_limit
    
    # Выбор игроков для турнира
    st.subheader("Выберите участников турнира")
    
    # Показываем список всех игроков с возможностью выбора
    if not st.session_state.players_df.empty:
        # Создаем список для отслеживания выбранных игроков
        selected_players = []
        
        # Проверяем ограничение на количество игроков
        players_limit = tournament_data.get('players_limit', 0)
        
        # Отображаем игроков в виде таблицы с чекбоксами
        for index, player in st.session_state.players_df.iterrows():
            col1, col2 = st.columns([1, 5])
            
            # Определяем, должен ли чекбокс быть активным
            disabled = False
            if players_limit > 0 and len(selected_players) >= players_limit:
                # Если достигнут лимит игроков и этот игрок еще не выбран - блокируем
                if player['id'] not in tournament_data.get('player_ids', []):
                    disabled = True
            
            with col1:
                selected = st.checkbox(
                    "", 
                    value=player['id'] in tournament_data.get('player_ids', []),
                    key=f"player_{player['id']}",
                    disabled=disabled
                )
            with col2:
                st.write(f"{player['name']} (Рейтинг: {player['rating']:.2f})")
            
            if selected:
                selected_players.append(player['id'])
        
        tournament_data['player_ids'] = selected_players
        
        # Отображаем количество выбранных игроков и лимит
        if players_limit > 0:
            st.write(f"Выбрано игроков: {len(selected_players)} / {players_limit}")
            
            # Если превышен лимит (могло произойти при изменении лимита после выбора)
            if len(selected_players) > players_limit:
                st.warning(f"Выбрано больше игроков, чем разрешено лимитом. Пожалуйста, снимите выбор с {len(selected_players) - players_limit} игроков.")
        else:
            st.write(f"Выбрано игроков: {len(selected_players)}")
        
        # Проверка минимального количества игроков для турнира
        min_players = 4
        if len(selected_players) < min_players:
            st.warning(f"Для создания турнира необходимо выбрать не менее {min_players} игроков.")
            can_start = False
        # Проверка соответствия лимиту
        elif players_limit > 0 and len(selected_players) > players_limit:
            st.warning(f"Превышен лимит игроков. Снимите выбор с {len(selected_players) - players_limit} игроков.")
            can_start = False
        else:
            can_start = True
            
        # Кнопка для генерации турнирной сетки
        if can_start:
            if st.button("Создать турнирную сетку", key="create_tournament_bracket"):
                # Генерируем турнирную сетку
                tournament_data = generate_bracket(tournament_data, selected_players)
                tournament_data['status'] = 'active'
                
                # Сохраняем список участников
                tournament_data['participants'] = selected_players
                
                # Обновляем турнир
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

def display_tournaments_list():
    """
    Отображает список всех турниров
    """
    st.subheader("Список турниров")
    
    # Инициализируем список турниров, если он еще не создан
    if 'tournaments_list' not in st.session_state:
        st.session_state.tournaments_list = []
        
        # Добавляем пример турниров для демонстрации
        sample_tournaments = [
            {
                'id': 1,
                'name': 'Весенний турнир 2025',
                'date': '2025-03-15',
                'duration_minutes': 120,
                'game_duration_minutes': 15,
                'players_count': 22,
                'players_limit': 24,
                'status': 'completed',
                'current_game': 0,
                'total_games': 8,
                'start_time': None,
                'pause_time': None,
                'elapsed_pause_time': 0,
                'participants': []
            },
            {
                'id': 2,
                'name': 'Летний кубок',
                'date': '2025-06-10',
                'duration_minutes': 90,
                'game_duration_minutes': 10,
                'players_count': 18,
                'players_limit': 20,
                'status': 'planned',
                'current_game': 0,
                'total_games': 6,
                'start_time': None,
                'pause_time': None,
                'elapsed_pause_time': 0,
                'participants': []
            }
        ]
        
        for t in sample_tournaments:
            st.session_state.tournaments_list.append(t)
            
    # Добавляем возможность удаления турниров
    with st.expander("Управление турнирами (для тестирования)"):
        st.markdown("**Удаление турнира**")
        tournaments_for_deletion = []
        
        for tournament in st.session_state.tournaments_list:
            tournaments_for_deletion.append(f"{tournament['id']} - {tournament['name']} ({tournament['date']})")
        
        if tournaments_for_deletion:
            selected_tournament = st.selectbox(
                "Выберите турнир для удаления", 
                tournaments_for_deletion,
                key="tournament_to_delete"
            )
            
            # Извлекаем ID из выбранной строки
            if selected_tournament:
                tournament_id = int(selected_tournament.split(' - ')[0])
                
                # Проверяем, не является ли выбранный турнир активным
                is_active = tournament_id == st.session_state.get('active_tournament_id')
                
                if is_active:
                    st.warning("Нельзя удалить активный турнир. Сначала завершите его.")
                
                # Создаем кнопку удаления, которая неактивна, если турнир активен
                confirm_deletion = st.button("Удалить выбранный турнир", key="confirm_deletion", disabled=is_active)
                
                if confirm_deletion:
                    # Находим индекс турнира в списке
                    tournament_idx = next(
                        (i for i, t in enumerate(st.session_state.tournaments_list) if t['id'] == tournament_id), 
                        None
                    )
                    
                    if tournament_idx is not None:
                        # Удаляем турнир
                        st.session_state.tournaments_list.pop(tournament_idx)
                        
                        # Сохраняем данные в файл
                        from storage import save_tournaments_data
                        save_tournaments_data()
                        
                        st.success("Турнир успешно удален!")
                        
                        # Если был выбран удаленный турнир, сбрасываем выбор
                        if st.session_state.get('selected_tournament_id') == tournament_id:
                            st.session_state.selected_tournament_id = None
                        
                        st.rerun()
    
    # Создаем таблицу турниров
    tournaments_df = pd.DataFrame(st.session_state.tournaments_list)
    
    if not tournaments_df.empty:
        # Форматируем и отображаем таблицу
        # Добавляем колонку для отображения статуса
        status_map = {
            'planned': 'Запланирован',
            'active': 'В процессе',
            'completed': 'Завершен'
        }
        tournaments_df['status_display'] = tournaments_df['status'].map(status_map)
        
        # Создаем редактируемую таблицу
        edited_df = st.data_editor(
            tournaments_df[['id', 'name', 'date', 'duration_minutes', 'game_duration_minutes', 'players_count', 'status_display']],
            column_config={
                "id": "№",
                "name": "Название турнира",
                "date": "Дата проведения",
                "duration_minutes": "Продолжительность (мин)",
                "game_duration_minutes": "Время игры (мин)",
                "players_count": "Кол-во участников",
                "status_display": "Статус"
            },
            disabled=["id", "status_display"],
            hide_index=True,
            use_container_width=True,
            key="tournaments_table"
        )
        
        # Добавляем кнопки действий для каждого турнира
        for idx, tournament in enumerate(st.session_state.tournaments_list):
            col1, col2, col3 = st.columns([3, 2, 2])
            
            # Получаем отображаемый статус
            status_map = {
                'planned': 'Запланирован',
                'active': 'В процессе',
                'completed': 'Завершен'
            }
            status_display = status_map.get(tournament['status'], tournament['status'])
            
            with col1:
                st.write(f"**{tournament['name']}** ({status_display})")
            
            with col2:
                # Кнопка действия в зависимости от статуса
                if tournament['status'] == 'planned':
                    if st.button(f"Начать турнир", key=f"start_tourney_{tournament['id']}"):
                        # Устанавливаем время игры в st.session_state
                        st.session_state.game_duration = tournament['game_duration_minutes']
                        # Запускаем таймер
                        start_tournament_timer(tournament['id'])
                        # Перезагружаем страницу
                        st.rerun()
                elif tournament['status'] == 'active':
                    is_paused = tournament['pause_time'] is not None
                    if is_paused:
                        if st.button(f"Возобновить", key=f"resume_tourney_{tournament['id']}"):
                            resume_tournament_timer(tournament['id'])
                            st.rerun()
                    else:
                        if st.button(f"Приостановить", key=f"pause_tourney_{tournament['id']}"):
                            pause_tournament_timer(tournament['id'])
                            st.rerun()
            
            with col3:
                # Показываем время для активных турниров
                if tournament['status'] == 'active':
                    elapsed_minutes, elapsed_seconds, remaining_minutes, remaining_seconds = calculate_tournament_time(tournament['id'])
                    st.write(f"⏱️ {elapsed_minutes:02d}:{elapsed_seconds:02d} / {remaining_minutes:02d}:{remaining_seconds:02d}")
                else:
                    st.write(f"Продолжительность: {tournament['duration_minutes']} мин")
                    
            st.divider()
        
        # Обрабатываем редактирование таблицы
        if not edited_df.equals(tournaments_df[['id', 'name', 'date', 'duration_minutes', 'game_duration_minutes', 'players_count', 'status_display']]):
            # Обновляем данные в session_state на основе изменений
            for index, row in edited_df.iterrows():
                tournament_id = row['id']
                tournament_idx = next((i for i, t in enumerate(st.session_state.tournaments_list) if t['id'] == tournament_id), None)
                
                if tournament_idx is not None:
                    st.session_state.tournaments_list[tournament_idx]['name'] = row['name']
                    st.session_state.tournaments_list[tournament_idx]['date'] = row['date']
                    st.session_state.tournaments_list[tournament_idx]['duration_minutes'] = row['duration_minutes']
                    st.session_state.tournaments_list[tournament_idx]['game_duration_minutes'] = row['game_duration_minutes']
                    
                    # Обновляем количество игроков и пересчитываем лимит, если он не был изменен вручную
                    old_players_count = st.session_state.tournaments_list[tournament_idx]['players_count']
                    
                    # Проверяем, существует ли ключ players_limit
                    if 'players_limit' not in st.session_state.tournaments_list[tournament_idx]:
                        # Если ключа нет, создаем его с тем же значением, что и players_count
                        st.session_state.tournaments_list[tournament_idx]['players_limit'] = old_players_count
                        old_players_limit = old_players_count
                    else:
                        old_players_limit = st.session_state.tournaments_list[tournament_idx]['players_limit']
                    
                    # Проверяем, был ли лимит игроков равен количеству (т.е. не изменялся вручную)
                    if old_players_count == old_players_limit:
                        # Если лимит не менялся вручную, то обновляем его вместе с count
                        st.session_state.tournaments_list[tournament_idx]['players_limit'] = row['players_count']
                    
                    # В любом случае обновляем количество игроков
                    st.session_state.tournaments_list[tournament_idx]['players_count'] = row['players_count']
            
            # Сохраняем данные в файл после внесения изменений
            from storage import save_tournaments_data
            save_tournaments_data()
    else:
        st.info("Нет доступных турниров")
    
    # Секция для создания нового турнира
    st.subheader("Создать новый турнир")
    
    col1, col2 = st.columns(2)
    with col1:
        new_name = st.text_input("Название турнира", key="new_tournament_name")
        new_date = st.date_input("Дата проведения", key="new_tournament_date")
    
    with col2:
        new_duration = st.number_input("Общая продолжительность (мин)", min_value=5, max_value=360, value=120, key="new_tournament_duration")
        new_game_duration = st.number_input("Время одной игры (мин)", min_value=1, max_value=60, value=15, key="new_tournament_game_duration")
    
    new_players_count = st.number_input("Количество участников", min_value=4, max_value=64, value=22, key="new_tournament_players_count")
    
    if st.button("Создать турнир", key="btn_create_tournament"):
        # Создаем новый ID как максимальный + 1
        new_id = 1
        if st.session_state.tournaments_list:
            new_id = max([t['id'] for t in st.session_state.tournaments_list]) + 1
        
        # Создаем новый турнир
        new_tournament = {
            'id': new_id,
            'name': new_name,
            'date': new_date.strftime('%Y-%m-%d'),
            'duration_minutes': new_duration,
            'game_duration_minutes': new_game_duration,
            'players_count': new_players_count,
            'players_limit': new_players_count,  # По умолчанию лимит равен планируемому количеству игроков
            'status': 'planned',
            'current_game': 0,
            'total_games': max(1, new_players_count // 4),
            'start_time': None,
            'pause_time': None,
            'elapsed_pause_time': 0,
            'participants': []  # Пустой список участников
        }
        
        # Добавляем в список
        st.session_state.tournaments_list.append(new_tournament)
        
        # Сохраняем данные в файл
        from storage import save_tournaments_data
        save_tournaments_data()
        
        st.success("Турнир успешно создан!")
        st.rerun()

def start_tournament_timer(tournament_id):
    """
    Запускает таймер для указанного турнира
    
    Parameters:
    - tournament_id: ID турнира
    """
    # Находим индекс турнира в списке
    tournament_idx = next(
        (i for i, t in enumerate(st.session_state.tournaments_list) if t['id'] == tournament_id), 
        None
    )
    
    if tournament_idx is not None:
        # Устанавливаем статус турнира в активный
        st.session_state.tournaments_list[tournament_idx]['status'] = 'active'
        # Записываем время начала
        st.session_state.tournaments_list[tournament_idx]['start_time'] = datetime.now()
        # Сбрасываем другие таймеры
        st.session_state.tournaments_list[tournament_idx]['pause_time'] = None
        st.session_state.tournaments_list[tournament_idx]['elapsed_pause_time'] = 0
        
        # Если в турнире еще нет участников, инициализируем пустой список
        if 'participants' not in st.session_state.tournaments_list[tournament_idx]:
            st.session_state.tournaments_list[tournament_idx]['participants'] = []
            
        # Сохраняем активный турнир в сессию
        st.session_state.active_tournament_id = tournament_id
        
        # Сохраняем данные в файл
        from storage import save_tournaments_data
        save_tournaments_data()
        
def pause_tournament_timer(tournament_id):
    """
    Приостанавливает таймер указанного турнира
    
    Parameters:
    - tournament_id: ID турнира
    """
    # Находим индекс турнира в списке
    tournament_idx = next(
        (i for i, t in enumerate(st.session_state.tournaments_list) if t['id'] == tournament_id), 
        None
    )
    
    if tournament_idx is not None and st.session_state.tournaments_list[tournament_idx]['start_time'] is not None:
        # Записываем время паузы
        st.session_state.tournaments_list[tournament_idx]['pause_time'] = datetime.now()
        
        # Сохраняем данные в файл
        from storage import save_tournaments_data
        save_tournaments_data()

def resume_tournament_timer(tournament_id):
    """
    Возобновляет таймер указанного турнира
    
    Parameters:
    - tournament_id: ID турнира
    """
    # Находим индекс турнира в списке
    tournament_idx = next(
        (i for i, t in enumerate(st.session_state.tournaments_list) if t['id'] == tournament_id), 
        None
    )
    
    if tournament_idx is not None and st.session_state.tournaments_list[tournament_idx]['pause_time'] is not None:
        # Рассчитываем время паузы
        pause_duration = (datetime.now() - st.session_state.tournaments_list[tournament_idx]['pause_time']).total_seconds()
        # Добавляем к общему времени пауз
        st.session_state.tournaments_list[tournament_idx]['elapsed_pause_time'] += pause_duration
        # Сбрасываем время паузы
        st.session_state.tournaments_list[tournament_idx]['pause_time'] = None
        
        # Сохраняем данные в файл
        from storage import save_tournaments_data
        save_tournaments_data()

def calculate_tournament_time(tournament_id):
    """
    Рассчитывает прошедшее и оставшееся время турнира
    
    Parameters:
    - tournament_id: ID турнира
    
    Returns:
    - tuple (elapsed_minutes, elapsed_seconds, remaining_minutes, remaining_seconds)
    """
    # Находим турнир в списке
    tournament = next(
        (t for t in st.session_state.tournaments_list if t['id'] == tournament_id), 
        None
    )
    
    if tournament is None:
        return 0, 0, 0, 0
        
    if tournament['start_time'] is None:
        return 0, 0, tournament['duration_minutes'], 0
    
    # Рассчитываем прошедшее время
    if tournament['pause_time'] is not None:
        # Если на паузе, используем время паузы
        elapsed_seconds_total = (tournament['pause_time'] - tournament['start_time']).total_seconds() - tournament['elapsed_pause_time']
    else:
        # Иначе используем текущее время
        elapsed_seconds_total = (datetime.now() - tournament['start_time']).total_seconds() - tournament['elapsed_pause_time']
    
    # Убедимся что elapsed_seconds_total не отрицательное
    elapsed_seconds_total = max(0, elapsed_seconds_total)
    
    # Рассчитываем минуты и секунды
    elapsed_minutes = int(elapsed_seconds_total // 60)
    elapsed_seconds = int(elapsed_seconds_total % 60)
    
    # Рассчитываем общую продолжительность в секундах
    total_duration_seconds = tournament['duration_minutes'] * 60
    
    # Рассчитываем оставшееся время
    remaining_seconds_total = max(0, total_duration_seconds - elapsed_seconds_total)
    
    # Рассчитываем оставшиеся минуты и секунды
    remaining_minutes = int(remaining_seconds_total // 60)
    remaining_seconds = int(remaining_seconds_total % 60)
    
    # Проверяем, если время вышло, обновляем статус
    if remaining_seconds_total <= 0 and tournament['status'] == 'active':
        # Находим индекс турнира в списке
        tournament_idx = next(
            (i for i, t in enumerate(st.session_state.tournaments_list) if t['id'] == tournament_id), 
            None
        )
        
        if tournament_idx is not None:
            # Обновляем статус на завершенный
            st.session_state.tournaments_list[tournament_idx]['status'] = 'completed'
            
            # Сохраняем данные в файл
            from storage import save_tournaments_data
            save_tournaments_data()
    
    return elapsed_minutes, elapsed_seconds, remaining_minutes, remaining_seconds

def display_tournament_history():
    """
    Отображает историю турниров и статистику игроков по турнирам
    """
    if 'tournament_history' not in st.session_state or not st.session_state.tournament_history:
        st.info("История турниров пуста. Проведите хотя бы один турнир для отображения истории.")
        return
    
    # Выбор турнира для просмотра истории
    tournament_options = []
    for tournament_id, data in st.session_state.tournament_history.items():
        if 'tournament_info' in data and 'tournament_name' in data['tournament_info']:
            tournament_options.append(f"{tournament_id} - {data['tournament_info']['tournament_name']}")
    
    if not tournament_options:
        st.info("Нет данных о завершенных турнирах.")
        return
    
    selected_tournament = st.selectbox("Выберите турнир для просмотра истории", tournament_options)
    
    if selected_tournament:
        # Извлекаем ID турнира из выбора
        tournament_id = int(selected_tournament.split(' - ')[0])
        
        # Получаем данные турнира
        tournament_data = st.session_state.tournament_history.get(tournament_id)
        
        if not tournament_data:
            st.error("Данные о турнире не найдены.")
            return
        
        # Отображаем информацию о турнире
        tournament_info = tournament_data.get('tournament_info', {})
        st.subheader(f"История турнира: {tournament_info.get('tournament_name', 'Неизвестный турнир')}")
        
        # Суммарная статистика турнира
        games = tournament_data.get('games', [])
        
        st.write(f"Всего игр: {len(games)}")
        
        # Таблица игр
        if games:
            games_data = []
            for i, game in enumerate(games):
                team_a_names = []
                team_b_names = []
                
                # Получаем имена игроков
                for player_id in game['team_a_players']:
                    player_name = st.session_state.players_df.loc[st.session_state.players_df['id'] == player_id, 'name'].values[0]
                    team_a_names.append(player_name)
                
                for player_id in game['team_b_players']:
                    player_name = st.session_state.players_df.loc[st.session_state.players_df['id'] == player_id, 'name'].values[0]
                    team_b_names.append(player_name)
                
                games_data.append({
                    'game_number': i + 1,
                    'court_number': game['court_number'],
                    'team_a': ', '.join(team_a_names),
                    'team_b': ', '.join(team_b_names),
                    'score': f"{game['team_a_score']} - {game['team_b_score']}",
                    'timestamp': game['timestamp']
                })
            
            games_df = pd.DataFrame(games_data)
            
            # Отображаем таблицу игр
            st.write("### Игры турнира")
            st.dataframe(
                games_df,
                column_config={
                    'game_number': 'Игра',
                    'court_number': 'Корт',
                    'team_a': 'Команда A',
                    'team_b': 'Команда B',
                    'score': 'Счет (A-B)',
                    'timestamp': 'Время'
                },
                use_container_width=True,
                hide_index=True
            )
        
        # Статистика игроков
        st.write("### Статистика игроков по турниру")
        
        player_stats = tournament_data.get('player_stats', {})
        
        if player_stats:
            player_stats_data = []
            
            for player_id, stats in player_stats.items():
                player_name = st.session_state.players_df.loc[st.session_state.players_df['id'] == player_id, 'name'].values[0]
                
                # Рассчитываем процент побед
                total_games = stats['wins'] + stats['losses']
                win_rate = (stats['wins'] / total_games * 100) if total_games > 0 else 0
                
                player_stats_data.append({
                    'player_name': player_name,
                    'games': total_games,
                    'wins': stats['wins'],
                    'losses': stats['losses'],
                    'win_rate': f"{win_rate:.1f}%",
                    'points_scored': stats['points_scored'],
                    'points_conceded': stats['points_conceded'],
                    'points_difference': stats['points_scored'] - stats['points_conceded']
                })
            
            # Сортируем по проценту побед
            player_stats_df = pd.DataFrame(player_stats_data)
            player_stats_df = player_stats_df.sort_values(by='wins', ascending=False)
            
            # Отображаем таблицу со статистикой
            st.dataframe(
                player_stats_df,
                column_config={
                    'player_name': 'Игрок',
                    'games': 'Игры',
                    'wins': 'Победы',
                    'losses': 'Поражения',
                    'win_rate': 'Процент побед',
                    'points_scored': 'Очки забиты',
                    'points_conceded': 'Очки пропущены',
                    'points_difference': 'Разница очков'
                },
                use_container_width=True,
                hide_index=True
            )

def display_tournament():
    """
    Main function for displaying tournament interface
    """
    # Add tabs for different sections
    tournament_tabs = st.tabs(["Tournament List", "Tournament History"])
    
    with tournament_tabs[0]:
        # Display list of all tournaments
        display_tournaments_list()
            
    with tournament_tabs[1]:
        # Display tournament history
        display_tournament_history()