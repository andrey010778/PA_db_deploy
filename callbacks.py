from dash import Input, Output
import plotly.graph_objects as go
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.express as px
import settings as st
import plotly.io as pio
from sqlalchemy import create_engine, exc
import os
from dotenv import load_dotenv

load_dotenv()

# Подключение к БД
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL не загружен из .env!")
    exit(1)

print("Пытаюсь подключиться к:", DATABASE_URL)

try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("✅ Успешное подключение!")
except exc.SQLAlchemyError as e:
    print(f"❌ Ошибка подключения: {e}")

#engine = create_engine(DATABASE_URL)

def get_data_from_db():
    query = "SELECT * FROM clear_dash_new"
    return pd.read_sql(query, engine)

# Установка кастомной паллетки цветов
pio.templates['custom'] = pio.templates['plotly'].update(
    layout=dict(colorway=st.MY_PALETTE)
)
pio.templates.default='custom'

def format_days(days):
    days = round(days)
    if days % 10 == 1 and days % 100 != 11:
        return f"{days} день"
    elif 2 <= days % 10 <= 4 and (days % 100 < 10 or days % 100 >= 20):
        return f"{days} дня"
    else:
        return f"{days} дней"

def register_callbacks(app):
    @app.callback(
        Output('dept-line-chart', 'figure'),
        Output('customer-bar-chart', 'figure'),
        Output('responsible-pie-chart', 'figure'),
        Output('stats-container', 'children'),
        Input('month-selector', 'value'),
        Input('dept-selector', 'value'),
        Input('customer-selector', 'value'),
        Input('responsible-selector', 'value')
    )
    def update_graphs(selected_months, selected_depts, selected_customers, selected_responsibles):
        # Загрузка данных из БД
        df = get_data_from_db()
        
        # Фильтрация данных
        filtered_df = df.copy()

        month_names = {
            '01': 'Январь', '02': 'Февраль', '03': 'Март', '04': 'Апрель',
            '05': 'Май', '06': 'Июнь', '07': 'Июль', '08': 'Август',
            '09': 'Сентябрь', '10': 'Октябрь', '11': 'Ноябрь', '12': 'Декабрь'}
        
        if selected_months:
            filtered_df = filtered_df[filtered_df['month'].isin(selected_months)]
        if selected_depts:
            filtered_df = filtered_df[filtered_df['Department'].isin(selected_depts)]
        if selected_customers:
            filtered_df = filtered_df[filtered_df['Customer'].isin(selected_customers)]
        if selected_responsibles:
            filtered_df = filtered_df[filtered_df['Responsible'].isin(selected_responsibles)]

        # Подготовка данных для графиков
        dept_data = filtered_df.groupby(['month', 'Department'])['Sum'].sum().reset_index()
        dept_data['month_name'] = dept_data['month'].str[5:7].map(month_names) + ' ' + dept_data['month'].str[:4]

        customer_data = filtered_df.groupby('Customer')['Sum'].sum().reset_index()
        customer_data = customer_data.sort_values('Sum', ascending=False)

        # 1. Линейный график по отделам
        line_fig = px.line(
            data_frame=dept_data,
            x='month_name',
            y='Sum',
            color='Department',
            labels={'amount': 'Сумма (руб)', 'month_name': 'Месяц', 'Department': 'Отделы'},
            markers=True
        )
        
        line_fig.add_trace(
            go.Scatter(
                x=dept_data['month_name'],
                y=dept_data.groupby('month_name')['Sum'].transform('mean'),
                name='Линия тренда',
                mode='lines+markers',
                line=dict(color='green', width=3, dash='dash'),
            )
        )
        
        line_fig.update_layout(
            xaxis_title='Месяцы',
            yaxis_title='Сумма, руб.',
            xaxis={'tickangle': 45},
            font=dict(family='Inter, sans-serif'),
            legend=dict(font=dict(size=st.GRAPH_FONT_SIZE)),
            paper_bgcolor=st.PAPER_BACKGROUND
        )

        # 2. Столбчатая диаграмма по заказчикам
        bar_fig = px.bar(
            data_frame=customer_data,            
            x='Customer',
            y='Sum',
            labels={'Sum': 'Сумма (руб)', 'Customer': 'Заказчик'},
        )

        bar_fig.update_layout(
            legend_title_text='Заказчики',
            xaxis_title='Заказчики',
            yaxis_title='Сумма, руб.',
            xaxis={'tickangle': 45},
            font=dict(family='Inter, sans-serif'),
            legend=dict(font=dict(size=st.GRAPH_FONT_SIZE)),
            paper_bgcolor=st.PAPER_BACKGROUND
        )

        # 3. Круговая диаграмма по ответственным
        pie_fig = px.pie(
            filtered_df.groupby('Responsible')['Sum'].sum().reset_index(),
            names='Responsible',
            values='Sum',
        )

        pie_fig.update_layout(
            legend_title_text='Ответственные',
            font=dict(family='Inter, sans-serif'),
            legend=dict(font=dict(size=st.GRAPH_FONT_SIZE)),
            paper_bgcolor=st.PAPER_BACKGROUND
        )

        # 4. Статистика
        stats = dbc.ListGroup([
            dbc.ListGroupItem(f'Количество счетов: {len(filtered_df)}'),
            dbc.ListGroupItem(f'Общая сумма: {filtered_df["Sum"].sum():,.0f} ₽'),
            dbc.ListGroupItem(f'Медианное значение по сумме счёта: {filtered_df["Sum"].median():,.0f} ₽'),
            dbc.ListGroupItem(f'Среднее значение по сумме счёта: {filtered_df["Sum"].mean():,.0f} ₽'),
            dbc.ListGroupItem(f'Среднее значение по выполнению: {format_days(filtered_df["Exec_time"].mean())}'),
            dbc.ListGroupItem(f'Среднее время оплаты: {format_days(filtered_df["Payment_time"].mean())}'),
        ])

        return line_fig, bar_fig, pie_fig, stats


