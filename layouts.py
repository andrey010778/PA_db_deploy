from dash import dcc, html
import dash_bootstrap_components as dbc
from sqlalchemy import create_engine, exc
import pandas as pd
import settings as st
import os
from dotenv import load_dotenv

load_dotenv()


# Подключение к БД
DATABASE_URL = os.getenv("DATABASE_URL")

# Подключение к БД
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("DATABASE_URL didn`t load from .env!")
    exit(1)

print("Try to connect:", DATABASE_URL)

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("Connection SUCCESS!")
except exc.SQLAlchemyError as e:
    print(f"Connection FAILED!: {e}")


def get_data_from_db():
    # Загрузка данных из PostgreSQL
    query = "SELECT * FROM clear_dash_new"
    df = pd.read_sql(query, engine)
    
    # Преобразование дат (если нужно)
    date_cols = ['Acc_date', 'Payment_date', 'Exec_date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
    
    return df

def get_layouts():
    df = get_data_from_db()
    
    # Русские названия месяцев для селектора
    month_names = {
        '01': 'Январь', '02': 'Февраль', '03': 'Март', '04': 'Апрель',
        '05': 'Май', '06': 'Июнь', '07': 'Июль', '08': 'Август',
        '09': 'Сентябрь', '10': 'Октябрь', '11': 'Ноябрь', '12': 'Декабрь'
    }
    
    # Формируем варианты для селектора месяцев
    month_options = [
        {'label': f"{month_names[mon[5:7]]} {mon[:4]}", 'value': mon} 
        for mon in sorted(df['month'].unique())
    ]
    
    # Получаем уникальные значения для фильтров
    months = sorted(df['month'].unique())
    departments = sorted(df['Department'].unique())
    customers = sorted(df['Customer'].unique())
    responsibles = sorted(df['Responsible'].unique())

    return dbc.Container(
        [
            # 1. Заголовок
            html.H1("Анализ дополнительных работ отдела эксплуатации", className='header-title'),

            # 2. Блок селекторов
            dbc.Card([
                dbc.CardHeader("Фильтры", className='filter-label'),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col(
                            dcc.Dropdown(
                                id="month-selector",
                                options=[{'label': m, 'value': m} for m in months],
                                value=months[-1:],
                                multi=True,
                                placeholder="Месяц...",
                                className='filter-dropdown',
                                style=st.DROPDOWN_STYLE,
                            ), width=3, xs=12, md=3
                        ),
                        dbc.Col(
                            dcc.Dropdown(
                                id="dept-selector",
                                options=[{'label': dep, 'value': dep} for dep in departments],
                                multi=True,
                                placeholder="Отдел...",
                                className='filter-dropdown',
                                style=st.DROPDOWN_STYLE,
                            ), width=3, xs=12, md=3
                        ),
                        dbc.Col(
                            dcc.Dropdown(
                                id="customer-selector",
                                options=[{'label': ctm, 'value': ctm} for ctm in customers],
                                multi=True,
                                placeholder="Заказчик...",
                                className='filter-dropdown',
                                style=st.DROPDOWN_STYLE,
                            ), width=3, xs=12, md=3
                        ),
                        dbc.Col(
                            dcc.Dropdown(
                                id="responsible-selector",
                                options=[{'label': resp, 'value': resp} for resp in responsibles],
                                multi=True,
                                placeholder="Ответственный...",
                                className='filter-dropdown',
                                style=st.DROPDOWN_STYLE,
                            ), width=3, xs=12, md=3
                        ),
                    ])
                ])
            ], className='filters-row'),

            # 3. Графики
            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader("Суммы по отделам"),
                        dbc.CardBody(dcc.Graph(id="dept-line-chart")),
                    ]), width=6, xs=12, md=6, className="mb-4"
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader("Суммы по заказчикам"),
                        dbc.CardBody(dcc.Graph(id="customer-bar-chart"))
                    ]), width=6, xs=12, md=6, className="mb-4"
                )
            ]),

            dbc.Row([
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader("Распределение по ответственным"),
                        dbc.CardBody(dcc.Graph(id="responsible-pie-chart"))
                    ]), width=6, xs=12, md=6, className="dash_graph"
                ),
                dbc.Col(
                    dbc.Card([
                        dbc.CardHeader("Статистика"),
                        dbc.CardBody(html.Div(id="stats-container"))
                    ]), width=6, xs=12, md=6, className="mb-4"
                )
            ])
        ],
        fluid=True
    )

