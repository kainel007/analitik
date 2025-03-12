import streamlit as st
import pandas as pd
from workalendar.europe import Russia
from data_manager import load_data

cal = Russia()

def get_working_days(year, month):
    return len([day for day in pd.date_range(f'{year}-{month:02d}-01', periods=31, freq='D')
                if day.month == month and cal.is_working_day(day)])

def app():
    st.title("Анализ посещений")

    # Загружаем данные из файла
    raw_data = load_data()
    if raw_data.empty:
        st.warning("Нет данных. Загрузите файл на странице 'Добавление данных'.")
        return

    # Приводим столбец 'Дата' к формату datetime
    raw_data['Дата'] = pd.to_datetime(raw_data['Дата'], errors='coerce')

    # Группируем данные по сотруднику и дате для расчёта статистики
    grouped = raw_data.groupby(['Сотрудник', 'Дата']).agg({
        'Время': ['min', 'max'],
        'Карта №': 'first'
    }).reset_index()
    grouped.columns = ['Сотрудник', 'Дата', 'Вход', 'Выход', 'Карта №']
    
    # Добавляем год и месяц для фильтрации
    grouped['Год'] = grouped['Дата'].dt.year
    grouped['Месяц'] = grouped['Дата'].dt.month

    # Выбор сотрудника, года и месяца через сайдбар
    employee = st.sidebar.selectbox("Выберите сотрудника", grouped['Сотрудник'].unique())
    years = sorted(grouped['Год'].unique(), reverse=True)
    selected_year = st.sidebar.selectbox("Выберите год", years)
    months = {1: 'Январь', 2: 'Февраль', 3: 'Март', 4: 'Апрель', 5: 'Май', 6: 'Июнь',
              7: 'Июль', 8: 'Август', 9: 'Сентябрь', 10: 'Октябрь', 11: 'Ноябрь', 12: 'Декабрь'}
    selected_month = st.sidebar.selectbox("Выберите месяц", list(months.keys()), format_func=lambda x: months[x])
    
    # Фильтрация данных
    filtered_data = grouped[(grouped['Сотрудник'] == employee) &
                              (grouped['Год'] == selected_year) &
                              (grouped['Месяц'] == selected_month)].copy()
    
    if not filtered_data.empty:
        working_days = get_working_days(selected_year, selected_month)
        total_days = filtered_data.shape[0]
        
        # Вычисление времени работы для каждой записи
        filtered_data['Время на работе'] = (
            pd.to_datetime(filtered_data['Выход'].astype(str), format='%H:%M:%S') -
            pd.to_datetime(filtered_data['Вход'].astype(str), format='%H:%M:%S')
        ).dt.total_seconds() / 60
        total_time = int(filtered_data['Время на работе'].sum())
        hours, minutes = divmod(total_time, 60)
        
        # Среднее время прихода и ухода
        try:
            avg_start = filtered_data['Вход'].apply(lambda x: pd.to_datetime(x, format='%H:%M:%S')).mean().time().strftime('%H:%M')
            avg_end = filtered_data['Выход'].apply(lambda x: pd.to_datetime(x, format='%H:%M:%S')).mean().time().strftime('%H:%M')
        except Exception:
            avg_start = avg_end = "N/A"
        
        avg_time_per_day = filtered_data['Время на работе'].mean()
        avg_hours, avg_minutes = divmod(int(avg_time_per_day), 60)
        avg_time_formatted = f"{avg_hours} часов {avg_minutes} минут"
        
        st.write(f"### {employee}")
        st.write(f"**Номер карты:** {filtered_data['Карта №'].iloc[0]}")
        st.write(f"**Рабочих дней:** {total_days} из {working_days}")
        st.write(f"**Общее время на работе:** {hours} часов {minutes} минут")
        st.write(f"**Среднее время прихода:** {avg_start}")
        st.write(f"**Среднее время ухода:** {avg_end}")
        st.write(f"**Среднее время нахождения в день:** {avg_time_formatted}")
        
        st.write("### Детальная статистика")
        filtered_data['Время на работе'] = filtered_data['Время на работе'].apply(
            lambda x: f"{int(x//60)} часов {int(x % 60)} минут"
        )
        filtered_data['Дата'] = filtered_data['Дата'].dt.strftime('%d-%m-%Y')
        
        # Сбрасываем индекс и заменяем его пустыми строками
        display_df = filtered_data[['Дата', 'Вход', 'Выход', 'Время на работе']].reset_index(drop=True)
        display_df.index = [''] * len(display_df)
        st.dataframe(display_df)
    else:
        st.warning("Нет данных за выбранный период.")
