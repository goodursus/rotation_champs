import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
import player_management as pm
import random
import numpy as np
from datetime import datetime

def generate_custom_layout():
    """
    Создает интерактивный интерфейс для ручного распределения игроков по кортам
    путем drag-and-drop
    """
    if 'players_df' not in st.session_state:
        st.error("Сначала добавьте игроков в список")
        return None

    players_df = st.session_state.players_df.copy()
    
    # Добавляем столбец для указания корта и позиции
    if 'court_assignment' not in players_df.columns:
        players_df['court_assignment'] = "Не распределен"
    
    if 'team' not in players_df.columns:
        players_df['team'] = ""
    
    # Создаем опции для выбора кортов
    num_players = len(players_df)
    num_courts = max(1, num_players // 4)
    
    court_options = ["Не распределен"] + [f"Корт {i+1}" for i in range(num_courts)] + ["Отдых"]
    team_options = ["", "A", "B"]
    
    # Создаем настройки для отображения таблицы
    gb = GridOptionsBuilder.from_dataframe(players_df[['name', 'rating', 'court_assignment', 'team']])
    
    # Настраиваем столбцы
    gb.configure_column('name', header_name='Имя игрока', editable=False)
    gb.configure_column('rating', header_name='Рейтинг', editable=False, width=80)
    
    # Столбец с выбором корта (выпадающий список)
    gb.configure_column(
        'court_assignment', 
        header_name='Корт', 
        editable=True,
        cellEditor='agSelectCellEditor',
        cellEditorParams={'values': court_options}
    )
    
    # Столбец с выбором команды (выпадающий список)
    gb.configure_column(
        'team', 
        header_name='Команда', 
        editable=True,
        cellEditor='agSelectCellEditor',
        cellEditorParams={'values': team_options},
        width=90
    )
    
    # Включаем drag-and-drop
    gb.configure_grid_options(rowDragManaged=True, animateRows=True)
    
    # Создаем таблицу
    grid_options = gb.build()
    
    # Отображаем интерактивную таблицу
    st.write("### Распределите игроков по кортам")
    st.write("Перемещайте строки перетаскиванием и назначайте корт и команду")
    
    # Отображаем таблицу с возможностью drag-and-drop
    grid_response = AgGrid(
        players_df,
        gridOptions=grid_options,
        update_mode=GridUpdateMode.MODEL_CHANGED,
        fit_columns_on_grid_load=True,
        height=400,
        allow_unsafe_jscode=True,
        enable_enterprise_modules=False
    )
    
    # Получаем обновленные данные
    updated_df = grid_response['data']
    
    # Кнопка для применения распределения
    if st.button("Применить распределение", key="apply_court_distribution"):
        # Проверяем корректность распределения
        validation_result, message = validate_court_assignment(updated_df)
        
        if validation_result:
            # Преобразуем пользовательские назначения в формат кортов
            courts = convert_assignments_to_courts(updated_df)
            st.session_state.courts = courts
            st.success("Распределение успешно применено!")
            return courts
        else:
            st.error(message)
            return None
    
    return None

def validate_court_assignment(df):
    """
    Проверяет корректность распределения игроков по кортам
    
    Returns:
    - (True, '') если распределение корректно
    - (False, error_message) если есть ошибки
    """
    # Проверяем, что все игроки распределены
    not_assigned = df[df['court_assignment'] == 'Не распределен']
    if len(not_assigned) > 0:
        return False, f"Есть нераспределенные игроки: {', '.join(not_assigned['name'].tolist())}"
    
    # Проверяем, что в каждом корте правильно назначены команды
    for court in df['court_assignment'].unique():
        if court == 'Отдых':
            continue  # Отдыхающие игроки не нуждаются в команде
            
        court_players = df[df['court_assignment'] == court]
        
        # Проверяем, что у всех игроков на корте назначена команда
        no_team = court_players[court_players['team'] == '']
        if len(no_team) > 0:
            return False, f"Игроки на корте {court} не имеют команды: {', '.join(no_team['name'].tolist())}"
        
        # Проверяем, что на корте есть обе команды
        team_a = court_players[court_players['team'] == 'A']
        team_b = court_players[court_players['team'] == 'B']
        
        if len(team_a) == 0:
            return False, f"На корте {court} нет игроков команды A"
        
        if len(team_b) == 0:
            return False, f"На корте {court} нет игроков команды B"
        
        # Проверяем, что в каждой команде не более 2 игроков
        if len(team_a) > 2:
            return False, f"В команде A на корте {court} слишком много игроков: {len(team_a)}"
        
        if len(team_b) > 2:
            return False, f"В команде B на корте {court} слишком много игроков: {len(team_b)}"
    
    return True, ''

def convert_assignments_to_courts(df):
    """
    Преобразует пользовательские назначения игроков в формат кортов
    
    Parameters:
    - df: DataFrame с распределением игроков
    
    Returns:
    - List of courts with player allocations
    """
    courts = []
    
    # Определяем уникальные корты (исключая "Не распределен")
    court_names = [c for c in df['court_assignment'].unique() if c != 'Не распределен']
    
    # Создаем корты
    for court_name in court_names:
        court_players = df[df['court_assignment'] == court_name]
        
        if court_name == 'Отдых':
            # Это корт для отдыха
            court = {
                'court_number': len(courts) + 1,
                'team_a': court_players['id'].tolist(),
                'team_b': [],
                'is_rest': True
            }
        else:
            # Обычный корт с двумя командами
            team_a = court_players[court_players['team'] == 'A']
            team_b = court_players[court_players['team'] == 'B']
            
            court = {
                'court_number': int(court_name.split(' ')[1]),
                'team_a': team_a['id'].tolist(),
                'team_b': team_b['id'].tolist(),
                'is_rest': False
            }
        
        courts.append(court)
    
    # Сортируем корты по номеру
    courts.sort(key=lambda x: x['court_number'])
    
    return courts

def generate_pickleball_score(team_a_advantage=0.0):
    """
    Генерирует счет по правилам pickleball (0-11 с правилом разницы в 2 очка при 10-10)
    
    Parameters:
    - team_a_advantage: Рейтинговое преимущество команды A, влияет на вероятность победы (float)
    
    Returns:
    - tuple (team_a_score, team_b_score)
    """
    # Базовая вероятность победы команды A (50% + влияние рейтинга)
    base_prob = 0.5 + (team_a_advantage / 20)  # Преимущество до ±50%
    team_a_wins = random.random() < base_prob
    
    # Генерация счета
    if team_a_wins:
        # Команда A побеждает - счет минимум 11
        team_a_score = random.randint(11, 15)
        # Команда B проигрывает, счет меньше
        if team_a_score == 11:
            # При счете 11, проигравший может иметь от 0 до 9
            team_b_score = random.randint(0, 9)
        else:
            # При счете больше 11, разница должна быть минимум 2 очка
            team_b_score = team_a_score - 2 - random.randint(0, 2)
    else:
        # Команда B побеждает - счет минимум 11
        team_b_score = random.randint(11, 15)
        # Команда A проигрывает, счет меньше
        if team_b_score == 11:
            # При счете 11, проигравший может иметь от 0 до 9
            team_a_score = random.randint(0, 9)
        else:
            # При счете больше 11, разница должна быть минимум 2 очка
            team_a_score = team_b_score - 2 - random.randint(0, 2)
    
    # Проверяем особый случай 10-10 (затягивание игры)
    if random.random() < 0.25:  # 25% шанс на затяжную игру
        # Счет сначала 10-10
        base_score = 10
        extra_points = random.randint(1, 4)  # Дополнительные очки
        
        # Добавляем очки, чтобы обеспечить разницу в 2
        if team_a_wins:
            # A побеждает (минимум 12-10)
            team_a_score = base_score + extra_points + 2
            team_b_score = base_score + extra_points
        else:
            # B побеждает (минимум 10-12)
            team_b_score = base_score + extra_points + 2
            team_a_score = base_score + extra_points
    
    # Финальная проверка - победитель должен иметь минимум 11 очков
    if team_a_score > team_b_score:
        team_a_score = max(11, team_a_score)
    else:
        team_b_score = max(11, team_b_score)
    
    # Обеспечиваем разницу минимум в 2 очка для победителя
    if team_a_score > team_b_score:
        if team_a_score - team_b_score < 2:
            team_a_score = team_b_score + 2
    else:
        if team_b_score - team_a_score < 2:
            team_b_score = team_a_score + 2
    
    return team_a_score, team_b_score


def auto_generate_results(consider_ratings=True, display_results=True, pickleball_scoring=True):
    """
    Автоматически генерирует случайные результаты игр для всех кортов
    и обновляет статистику игроков
    
    Parameters:
    - consider_ratings: Если True, результаты будут генерироваться с учетом рейтингов игроков
    - display_results: Если True, результаты будут выведены на экран
    - pickleball_scoring: Если True, использует систему счета pickleball (0-11)
    
    Returns:
    - List of generated results
    """
    if 'courts' not in st.session_state or not st.session_state.courts:
        if display_results:
            st.error("Сначала распределите игроков по кортам")
        return None
    
    courts = st.session_state.courts
    players_df = st.session_state.players_df
    
    results = []
    
    # Генерируем случайные результаты для каждого корта
    for i, court in enumerate(courts):
        if court['is_rest']:
            continue
        
        if consider_ratings and not st.session_state.get('random_results_only', False):
            # Вычисляем средний рейтинг команд
            team_a_ratings = [players_df.loc[players_df['id'] == pid, 'rating'].values[0] for pid in court['team_a']]
            team_b_ratings = [players_df.loc[players_df['id'] == pid, 'rating'].values[0] for pid in court['team_b']]
            
            team_a_avg_rating = sum(team_a_ratings) / len(team_a_ratings) if team_a_ratings else 0
            team_b_avg_rating = sum(team_b_ratings) / len(team_b_ratings) if team_b_ratings else 0
            
            # Нормализуем разницу рейтингов для влияния на результат
            rating_diff = team_a_avg_rating - team_b_avg_rating
            
            if pickleball_scoring:
                # Генерируем счет по правилам pickleball
                team_a_score, team_b_score = generate_pickleball_score(float(rating_diff))
            else:
                # Старая логика для других систем счета
                rating_advantage = min(10, max(-10, rating_diff / 10))  # Максимум ±10 очков влияния
                base_score = random.randint(10, 18)
                team_a_score = max(5, min(21, int(base_score + rating_advantage + random.randint(-2, 2))))
                noise = int(np.random.normal(0, 3))
                team_b_score = max(5, min(21, int(base_score - rating_advantage + noise)))
                
                # Обеспечиваем минимальную разницу в 2 очка для победителя
                if team_a_score > team_b_score and team_a_score - team_b_score < 2:
                    team_a_score = team_b_score + 2
                elif team_b_score > team_a_score and team_b_score - team_a_score < 2:
                    team_b_score = team_a_score + 2
        else:
            # Полностью случайная генерация
            if pickleball_scoring:
                team_a_score, team_b_score = generate_pickleball_score(0.0)  # Без преимущества
            else:
                team_a_score = random.randint(5, 21)
                score_diff = int(np.random.normal(0, 5))
                team_b_score = max(5, min(21, team_a_score + score_diff))
                
                # Обеспечиваем минимальную разницу в 2 очка для победителя
                if team_a_score > team_b_score and team_a_score - team_b_score < 2:
                    team_a_score = team_b_score + 2
                elif team_b_score > team_a_score and team_b_score - team_a_score < 2:
                    team_b_score = team_a_score + 2
        
        # Добавляем результаты
        results.append({
            'court_idx': i,
            'team_a_score': team_a_score,
            'team_b_score': team_b_score
        })
    
    # Применяем результаты
    for result in results:
        pm.update_player_stats(
            result['court_idx'],
            result['team_a_score'],
            result['team_b_score']
        )
    
    if display_results:
        st.success(f"Автоматически сгенерированы результаты для {len(results)} кортов")
        
        # Отображаем сгенерированные результаты
        if results:
            st.write("### Сгенерированные результаты:")
            for i, result in enumerate(results):
                court_idx = result['court_idx']
                court = courts[court_idx]
                
                # Получаем имена игроков
                player_names_a = [st.session_state.players_df.loc[st.session_state.players_df['id'] == pid, 'name'].values[0] 
                               for pid in court['team_a']]
                player_names_b = [st.session_state.players_df.loc[st.session_state.players_df['id'] == pid, 'name'].values[0] 
                               for pid in court['team_b']]
                
                team_a_str = ", ".join(player_names_a)
                team_b_str = ", ".join(player_names_b)
                
                # Определяем стиль отображения результата в зависимости от победителя
                result_style = ""
                if result['team_a_score'] > result['team_b_score']:
                    result_style = f"**{team_a_str}** ({result['team_a_score']}) vs {team_b_str} ({result['team_b_score']})"
                else:
                    result_style = f"{team_a_str} ({result['team_a_score']}) vs **{team_b_str}** ({result['team_b_score']})"
                
                st.write(f"**Корт {court['court_number']}:** {result_style}")
    
    # Пересчитываем рейтинги игроков
    pm.calculate_ratings()
    
    # Сохраняем результаты для истории
    if 'game_history' not in st.session_state:
        st.session_state.game_history = []
    
    # Добавляем запись в историю игр
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    for result in results:
        court_idx = result['court_idx']
        court = courts[court_idx]
        
        # Формируем запись истории
        history_entry = {
            'timestamp': timestamp,
            'court_number': court['court_number'],
            'team_a_players': court['team_a'],
            'team_b_players': court['team_b'],
            'team_a_score': result['team_a_score'],
            'team_b_score': result['team_b_score']
        }
        
        st.session_state.game_history.append(history_entry)
    
    return results

def display_player_performance():
    """
    Отображает графики и статистику производительности игроков на основе истории игр
    """
    if 'game_history' not in st.session_state or not st.session_state.game_history:
        st.info("Пока нет данных об играх. Проведите несколько игр для отображения статистики.")
        return
    
    st.write("### История результатов игр")
    
    # Конвертируем историю игр в DataFrame для удобства анализа
    history_data = []
    for entry in st.session_state.game_history:
        # Определяем победителя
        team_a_won = entry['team_a_score'] > entry['team_b_score']
        
        # Добавляем записи для всех игроков в команде A
        for player_id in entry['team_a_players']:
            player_name = st.session_state.players_df.loc[st.session_state.players_df['id'] == player_id, 'name'].values[0]
            history_data.append({
                'timestamp': entry['timestamp'],
                'player_id': player_id,
                'player_name': player_name,
                'team': 'A',
                'opponent_team': 'B',
                'court': entry['court_number'],
                'score': entry['team_a_score'],
                'opponent_score': entry['team_b_score'],
                'won': team_a_won,
                'point_diff': entry['team_a_score'] - entry['team_b_score']
            })
        
        # Добавляем записи для всех игроков в команде B
        for player_id in entry['team_b_players']:
            player_name = st.session_state.players_df.loc[st.session_state.players_df['id'] == player_id, 'name'].values[0]
            history_data.append({
                'timestamp': entry['timestamp'],
                'player_id': player_id,
                'player_name': player_name,
                'team': 'B',
                'opponent_team': 'A',
                'court': entry['court_number'],
                'score': entry['team_b_score'],
                'opponent_score': entry['team_a_score'],
                'won': not team_a_won,
                'point_diff': entry['team_b_score'] - entry['team_a_score']
            })
    
    history_df = pd.DataFrame(history_data)
    
    # Преобразуем строку времени в datetime
    history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])
    
    # Отображаем последние результаты
    st.write("#### Последние результаты игр")
    
    # Группируем по времени и корту для отображения последних игр
    last_games = history_df.sort_values('timestamp', ascending=False)
    
    # Получаем уникальные временные метки (сессии игр)
    sessions = last_games['timestamp'].unique()
    
    for i, session in enumerate(sessions[:5]):  # Показываем до 5 последних сессий
        session_games = last_games[last_games['timestamp'] == session]
        
        # Группируем по корту
        courts = session_games['court'].unique()
        
        st.write(f"**Сессия {i+1}:** {session}")
        
        for court in courts:
            court_data = session_games[session_games['court'] == court]
            
            # Получаем игроков команды A и B
            team_a = court_data[court_data['team'] == 'A']
            team_b = court_data[court_data['team'] == 'B']
            
            if len(team_a) > 0 and len(team_b) > 0:
                team_a_players = ", ".join(team_a['player_name'].unique())
                team_b_players = ", ".join(team_b['player_name'].unique())
                
                team_a_score = team_a['score'].values[0]
                team_b_score = team_b['score'].values[0]
                
                # Определяем стиль отображения в зависимости от победителя
                if team_a_score > team_b_score:
                    result = f"**{team_a_players}** ({team_a_score}) vs {team_b_players} ({team_b_score})"
                else:
                    result = f"{team_a_players} ({team_a_score}) vs **{team_b_players}** ({team_b_score})"
                
                st.write(f"**Корт {int(court)}:** {result}")
    
    # Статистика по игрокам
    st.write("#### Статистика игроков")
    player_stats = history_df.groupby('player_name').agg({
        'won': ['sum', 'count'],
        'point_diff': 'mean'
    }).reset_index()
    
    player_stats.columns = ['player_name', 'wins', 'games', 'avg_point_diff']
    player_stats['win_rate'] = player_stats['wins'] / player_stats['games'] * 100
    player_stats['win_rate'] = player_stats['win_rate'].round(1)
    player_stats['avg_point_diff'] = player_stats['avg_point_diff'].round(1)
    
    # Сортируем по проценту побед
    player_stats = player_stats.sort_values('win_rate', ascending=False)
    
    # Создаем удобную таблицу
    player_stats_display = player_stats[['player_name', 'wins', 'games', 'win_rate', 'avg_point_diff']]
    player_stats_display.columns = ['Игрок', 'Победы', 'Игры', 'Процент побед', 'Средняя разница']
    
    st.dataframe(player_stats_display)
    
    # Добавляем график изменения рейтинга/результатов со временем
    if len(sessions) > 1:
        st.write("#### Динамика результатов")
        
        # Добавляем выбор игрока для анализа
        players = history_df['player_name'].unique()
        selected_player = st.selectbox("Выберите игрока для анализа", players)
        
        if selected_player:
            # Получаем данные для выбранного игрока
            player_data = history_df[history_df['player_name'] == selected_player].sort_values('timestamp')
            
            # Подготавливаем данные для графиков
            chart_data = {
                'date': player_data['timestamp'],
                'point_diff': player_data['point_diff'].rolling(window=5, min_periods=1).mean(),
                'cumulative_wins': player_data['won'].cumsum(),
                'win_rate': (player_data['won'].cumsum() / range(1, len(player_data) + 1)) * 100
            }
            
            chart_df = pd.DataFrame(chart_data)
            
            # Создаем вкладки для разных метрик
            metric_tabs = st.tabs(["Разница очков", "Накопительные победы", "Процент побед", "Рейтинг"])
            
            with metric_tabs[0]:
                st.write(f"#### Средняя разница очков для {selected_player}")
                st.line_chart(chart_df.set_index('date')['point_diff'], use_container_width=True)
                st.info("График показывает скользящее среднее разницы очков за последние 5 игр")
            
            with metric_tabs[1]:
                st.write(f"#### Накопительное количество побед для {selected_player}")
                st.line_chart(chart_df.set_index('date')['cumulative_wins'], use_container_width=True)
            
            with metric_tabs[2]:
                st.write(f"#### Динамика процента побед для {selected_player}")
                st.line_chart(chart_df.set_index('date')['win_rate'], use_container_width=True)
                st.info("График показывает, как меняется процент побед с накоплением сыгранных игр")
                
            with metric_tabs[3]:
                st.write(f"#### Динамика рейтинга для {selected_player}")
                
                # Получаем ID игрока
                player_id = player_data['player_id'].iloc[0]
                
                # Подготавливаем историю рейтинга, если она есть
                if 'rating_history' in st.session_state and player_id in st.session_state.rating_history:
                    rating_history = st.session_state.rating_history[player_id]
                    
                    # Создаем DataFrame для графика
                    rating_df = pd.DataFrame({
                        'date': [entry['timestamp'] for entry in rating_history],
                        'rating': [entry['rating'] for entry in rating_history]
                    })
                    
                    # Преобразуем дату в формат datetime
                    rating_df['date'] = pd.to_datetime(rating_df['date'])
                    
                    # Строим график
                    st.line_chart(rating_df.set_index('date')['rating'], use_container_width=True)
                    
                    # Выводим текущий рейтинг
                    current_rating = st.session_state.players_df.loc[st.session_state.players_df['id'] == player_id, 'rating'].values[0]
                    st.info(f"Текущий рейтинг: {current_rating:.2f}")
                else:
                    st.info("История рейтинга пока не доступна. Для отслеживания динамики рейтинга необходимо провести больше игр.")


def display_court_designer():
    """
    Основная функция для отображения дизайнера кортов
    """
    st.subheader("Дизайнер расположения кортов")
    
    # Создаем вкладки для различных функций
    design_tab, auto_tab, stats_tab = st.tabs(["Ручное распределение", "Автоматическое тестирование", "Статистика игр"])
    
    with design_tab:
        generate_custom_layout()
    
    with auto_tab:
        st.write("### Автоматическое тестирование")
        st.write("Автоматически генерирует случайные результаты игр для всех кортов.")
        
        # Настройки генерации результатов
        with st.expander("Настройки генерации результатов"):
            # Опция для учета рейтингов при генерации
            if 'consider_ratings_for_results' not in st.session_state:
                st.session_state.consider_ratings_for_results = True
                
            st.session_state.consider_ratings_for_results = st.checkbox(
                "Учитывать рейтинг игроков при генерации результатов",
                value=st.session_state.consider_ratings_for_results
            )
            
            if st.session_state.consider_ratings_for_results:
                st.info("""
                    Результаты игр генерируются с учетом рейтинга игроков. 
                    Команды с более высоким средним рейтингом имеют больше шансов на победу.
                """)
            else:
                st.info("Результаты генерируются полностью случайно без учета рейтинга игроков.")
                
            # Опция для активации авто-генерации при окончании таймера
            st.session_state.auto_results_on_timer_end = st.checkbox(
                "Генерировать результаты автоматически при окончании таймера", 
                value=st.session_state.get('auto_results_on_timer_end', False)
            )
            
            if st.session_state.auto_results_on_timer_end:
                st.success("Автоматическая генерация при окончании таймера активирована!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Сгенерировать случайные результаты", key="btn_generate_random_results", use_container_width=True):
                auto_generate_results(
                    consider_ratings=st.session_state.consider_ratings_for_results,
                    display_results=True
                )
        
        with col2:
            game_active = st.session_state.get('game_active', False)
            game_paused = st.session_state.get('game_paused', False)
            
            if game_active:
                status = "▶️ Активен" if not game_paused else "⏸️ Приостановлен"
                st.info(f"Статус таймера: {status}")
                
                if game_paused:
                    if st.button("Возобновить таймер", key="btn_resume_timer_designer", use_container_width=True):
                        import timer as tm
                        tm.resume_game()
                        st.rerun()
                else:
                    if st.button("Приостановить таймер", key="btn_pause_timer_designer", use_container_width=True):
                        import timer as tm
                        tm.pause_game()
                        st.rerun()
            else:
                if st.button("Запустить таймер", key="btn_start_timer_designer", use_container_width=True):
                    import timer as tm
                    tm.start_game()
                    st.rerun()
    
    with stats_tab:
        display_player_performance()