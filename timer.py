import streamlit as st
import time
from datetime import datetime, timedelta

def start_game():
    """
    Start a new game
    """
    # Полностью сбрасываем таймер и затем устанавливаем его в активное состояние
    st.session_state.game_active = True
    st.session_state.game_paused = False
    st.session_state.start_time = datetime.now()
    st.session_state.elapsed_pause_time = 0
    
    # Сбрасываем счетчики
    if 'update_counter' not in st.session_state:
        st.session_state.update_counter = 0
    else:
        st.session_state.update_counter = 0
    
    # Увеличиваем счетчик игр для активного турнира
    active_tournament_id = st.session_state.get('active_tournament_id')
    if active_tournament_id is not None:
        # Находим индекс турнира в списке
        tournament_idx = next(
            (i for i, t in enumerate(st.session_state.tournaments_list) if t['id'] == active_tournament_id), 
            None
        )
        if tournament_idx is not None:
            # Увеличиваем счетчик текущей игры
            current_game = st.session_state.tournaments_list[tournament_idx].get('current_game', 0)
            st.session_state.tournaments_list[tournament_idx]['current_game'] = current_game + 1
    
    # Выводим логи для диагностики
    print(f"Игра запущена: {datetime.now()}")

def pause_game():
    """
    Pause the current game
    """
    # Проверяем, что игра активна и не на паузе
    if st.session_state.game_active and not st.session_state.game_paused:
        st.session_state.game_paused = True
        st.session_state.pause_time = datetime.now()
        
        # Выводим логи для диагностики
        print(f"Игра приостановлена: {datetime.now()}")

def resume_game():
    """
    Resume a paused game
    """
    # Проверяем, что игра активна и находится на паузе
    if st.session_state.game_active and st.session_state.game_paused:
        # Защита от случая, когда pause_time не был правильно установлен
        if st.session_state.pause_time is None:
            st.session_state.pause_time = datetime.now()
        
        # Рассчитываем длительность паузы
        pause_duration = (datetime.now() - st.session_state.pause_time).total_seconds()
        
        # Добавляем к общему времени на паузе
        st.session_state.elapsed_pause_time += pause_duration
        
        # Снимаем с паузы
        st.session_state.game_paused = False
        
        # Выводим логи для диагностики
        print(f"Игра возобновлена: {datetime.now()}, пауза длилась {pause_duration:.2f} сек")

def reset_game():
    """
    Reset the game timer
    """
    # Полностью сбрасываем все переменные состояния игры
    st.session_state.game_active = False
    st.session_state.game_paused = False
    st.session_state.start_time = None
    st.session_state.pause_time = None
    st.session_state.elapsed_pause_time = 0
    
    # Увеличиваем счетчик сбросов для визуального индикатора
    if 'reset_counter' not in st.session_state:
        st.session_state.reset_counter = 0
    st.session_state.reset_counter += 1
    
    # Сбрасываем счетчик обновлений
    st.session_state.update_counter = 0
    
    # Устанавливаем флаг завершения игры - требуется ротация перед следующей игрой
    st.session_state.game_ended = True
    
    # Выводим логи для диагностики
    print(f"Таймер сброшен: {datetime.now()}")

def calculate_game_time():
    """
    Calculate elapsed and remaining game time with seconds precision
    
    Returns:
    - elapsed_minutes: Minutes elapsed since game started
    - elapsed_seconds: Seconds part of elapsed time
    - remaining_minutes: Minutes remaining in the game
    - remaining_seconds: Seconds part of remaining time
    """
    if not st.session_state.game_active or st.session_state.start_time is None:
        return 0, 0, st.session_state.game_duration, 0
    
    # Безопасная обработка случая, когда игра активна, но время паузы не определено
    if st.session_state.game_paused:
        if st.session_state.pause_time is None:
            st.session_state.pause_time = datetime.now()
            
        # If game is paused, calculate elapsed time up to when it was paused
        elapsed_seconds_total = (st.session_state.pause_time - st.session_state.start_time).total_seconds() - st.session_state.elapsed_pause_time
    else:
        # Calculate elapsed time considering any pauses
        elapsed_seconds_total = (datetime.now() - st.session_state.start_time).total_seconds() - st.session_state.elapsed_pause_time
    
    # Убедимся, что elapsed_seconds_total не отрицательное
    elapsed_seconds_total = max(0, elapsed_seconds_total)
    
    # Calculate elapsed minutes and seconds
    elapsed_minutes = int(elapsed_seconds_total // 60)
    elapsed_seconds = int(elapsed_seconds_total % 60)
    
    # Calculate total game duration in seconds
    total_duration_seconds = st.session_state.game_duration * 60
    
    # Calculate remaining seconds
    remaining_seconds_total = max(0, total_duration_seconds - elapsed_seconds_total)
    
    # Calculate remaining minutes and seconds
    remaining_minutes = int(remaining_seconds_total // 60)
    remaining_seconds = int(remaining_seconds_total % 60)
    
    # Проверяем, нужно ли автоматически завершить игру и сгенерировать результаты
    if st.session_state.game_active and not st.session_state.game_paused:
        if remaining_seconds_total <= 0:
            # Время игры истекло, немедленно сбрасываем индикатор активности
            # (чтобы другие функции видели, что таймер не активен)
            st.session_state.game_active = False
            
            # Отложенный импорт во избежание циклических зависимостей
            try:
                # Проверяем, активирован ли режим автоматической генерации результатов
                if st.session_state.get('auto_results_on_timer_end', False):
                    import court_designer as cd
                    # Генерируем результаты с настройками pickleball
                    results = cd.auto_generate_results(
                        consider_ratings=st.session_state.get('consider_ratings_for_results', True),
                        display_results=False,  # Не отображаем результаты на странице дизайнера
                        pickleball_scoring=True  # Используем правила pickleball
                    )
                    
                    # Сохраняем результаты в session_state для заполнения полей ввода
                    if results and not st.session_state.get('pending_results', None):
                        st.session_state.pending_results = results
                    
                    # Отмечаем, что нужно показать уведомление
                    st.session_state.show_results_notification = True
            except Exception as e:
                print(f"Ошибка при автоматической генерации результатов: {str(e)}")
            
            # Отмечаем, что таймер нужно полностью сбросить при следующем обновлении страницы
            st.session_state.timer_needs_reset = True
    
    return elapsed_minutes, elapsed_seconds, remaining_minutes, remaining_seconds
