import streamlit as st
import pandas as pd
import datetime
from data_manager import load_data, save_data

def process_file(uploaded_file, document_name):
    # Определим ожидаемые столбцы и подстроки для их поиска
    expected_columns = {
        'Сотрудник': ['Сотрудник'],
        'Дата': ['Дата'],
        'Время': ['Время'],
        'Карта №': ['Карта']
    }

    try:
        # Читаем первые 5 строк без заголовков для поиска строки с заголовками
        uploaded_file.seek(0)
        sample = pd.read_excel(uploaded_file, header=None, nrows=5)
        
        header_row_idx = None
        header_mapping = None  # Сопоставление: требуемое имя -> найденное название в файле
        # Перебираем первые 5 строк, чтобы найти строку, где все нужные столбцы присутствуют по подстроке
        for i in range(sample.shape[0]):
            row_values = sample.iloc[i].astype(str).tolist()
            current_mapping = {}
            for key, substrings in expected_columns.items():
                for header in row_values:
                    if any(sub.lower() in header.lower() for sub in substrings):
                        current_mapping[key] = header
                        break
            if len(current_mapping) == len(expected_columns):
                header_row_idx = i
                header_mapping = current_mapping
                break
        
        if header_row_idx is None:
            st.error("Не удалось найти строку с заголовками, содержащими все необходимые столбцы.")
            return None
        
        # Считываем весь файл с найденной строкой заголовков
        uploaded_file.seek(0)
        df = pd.read_excel(uploaded_file, header=header_row_idx)
        # Удаляем автоматически сгенерированные столбцы (например, 'Unnamed: 0')
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    except Exception as e:
        st.error(f"Ошибка при чтении файла: {e}")
        return None

    # Переименовываем найденные столбцы согласно ожидаемым именам
    df = df.rename(columns={v: k for k, v in header_mapping.items()})
    
    # Проверяем, что после переименования остались все необходимые столбцы
    required_columns = list(expected_columns.keys())
    if not set(required_columns).issubset(set(df.columns)):
        st.error("В загруженном файле отсутствуют необходимые столбцы после переименования. Проверьте правильность заголовков.")
        return None

    # Оставляем только необходимые столбцы
    df = df[required_columns]
    
    # Преобразуем столбец 'Дата' (предполагается формат dd.mm.yyyy, день первым)
    df['Дата'] = pd.to_datetime(df['Дата'], errors='coerce', dayfirst=True)
    
    # Преобразуем столбец 'Время'
    try:
        def parse_time(val):
            if pd.isnull(val):
                return None
            # Если значение числовое, предположим, что это дробь дня (Excel)
            if isinstance(val, (int, float)):
                try:
                    seconds = float(val) * 24 * 3600
                    return (datetime.datetime(1900, 1, 1) + datetime.timedelta(seconds=seconds)).time()
                except Exception:
                    return None
            # Если значение строковое, пробуем форматы '%H:%M:%S' и '%H:%M'
            try:
                parsed = pd.to_datetime(val, format='%H:%M:%S', errors='coerce')
                if pd.isnull(parsed):
                    parsed = pd.to_datetime(val, format='%H:%M', errors='coerce')
                if pd.isnull(parsed):
                    return None
                return parsed.time()
            except Exception:
                return None
        df['Время'] = df['Время'].apply(parse_time)
        # Преобразуем время в строку для обеспечения совместимости с Arrow
        df['Время'] = df['Время'].apply(lambda t: t.strftime('%H:%M:%S') if t is not None else None)
    except Exception:
        st.error("Ошибка при обработке столбца 'Время'.")
        return None

    # Добавляем информацию о документе
    df['Документ'] = document_name
    return df

def app():
    st.title("Добавление данных")

    # Загружаем сохранённые данные из файла
    saved_data = load_data()
    if not saved_data.empty:
        st.success("Обнаружены сохранённые данные!")
        st.write("Загруженные данные:")
        st.write(saved_data)

    # Возможность удаления ранее добавленного документа
    if not saved_data.empty and 'Документ' in saved_data.columns:
        documents = saved_data['Документ'].unique().tolist()
        st.subheader("Удаление ранее добавленного документа")
        selected_doc = st.selectbox("Выберите документ для удаления", documents)
        if st.button("Удалить выбранный документ"):
            updated_data = saved_data[saved_data['Документ'] != selected_doc]
            save_data(updated_data)
            st.success(f"Документ '{selected_doc}' удалён!")
            saved_data = updated_data  # Обновляем сохранённые данные

    st.subheader("Загрузка нового файла")
    uploaded_file = st.file_uploader("Загрузите xlsx-файл", type=["xlsx"])
    if uploaded_file is not None:
        new_data = process_file(uploaded_file, uploaded_file.name)
        if new_data is not None:
            # Объединяем новые данные с уже сохранёнными
            if not saved_data.empty:
                combined_data = pd.concat([saved_data, new_data], ignore_index=True)
            else:
                combined_data = new_data
            combined_data.drop_duplicates(inplace=True)
            save_data(combined_data)
            st.success("Данные успешно загружены и сохранены!")
            st.write("Обработанные данные:")
            st.write(combined_data)
    elif saved_data.empty:
        st.warning("Нет данных. Загрузите файл.")
