import pandas as pd
import os

DATA_FILE = "attendance_data.xlsx"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_excel(DATA_FILE)
    # Если файл не существует – возвращаем пустой DataFrame с нужными столбцами
    return pd.DataFrame(columns=['Сотрудник', 'Дата', 'Время', 'Карта №', 'Документ'])

def save_data(data: pd.DataFrame):
    data.to_excel(DATA_FILE, index=False)
