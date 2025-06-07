from dash import Input, Output, html
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
    query = "SELECT * FROM clear_dash_new"
    return pd.read_sql(query, engine)

# Установка кастомной паллетки цветов
pio.templates['custom'] = pio.templates['plotly'].update(
    layout=dict(colorway=st.MY_PALETTE)
)
pio.templates.default='custom'

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
        # Загрузка данных
        df = get_data_from_db()
        
        # Фильтрация
        filtered_df = df.copy()
        if selected_months:
            filtered_df = filtered_df[filtered_df['month'].isin(selected_months)]
        if selected_depts:
            filtered_df = filtered_df[filtered_df['Department'].isin(selected_depts)]
        if selected_customers:
            filtered_df = filtered_df[filtered_df['Customer'].isin(selected_customers)]
        if selected_responsibles:
            filtered_df = filtered_df[filtered_df['Responsible'].isin(selected_responsibles)]

        # Подготовка данных для линейного графика
        dept_data = filtered_df.groupby(['month', 'Department'])['Sum'].sum().reset_index()
        
        # Преобразуем текстовый формат YYYY-MM в дату
        dept_data['date'] = pd.to_datetime(dept_data['month'], format='%Y-%m')
        
        # Создаем русские названия месяцев
        month_translate = {
            'January': 'Январь', 'February': 'Февраль', 'March': 'Март',
            'April': 'Апрель', 'May': 'Май', 'June': 'Июнь',
            'July': 'Июль', 'August': 'Август', 'September': 'Сентябрь',
            'October': 'Октябрь', 'November': 'Ноябрь', 'December': 'Декабрь'
        }
        
        dept_data['month_name'] = (dept_data['date'].dt.month_name().map(month_translate) + 
                                 ' ' + 
                                 dept_data['date'].dt.year.astype(str))
        
        # Сортируем по дате
        dept_data = dept_data.sort_values('date')
        month_order = dept_data['month_name'].unique().tolist()

        # 1. Линейный график
        line_fig = px.line(
            dept_data,
            x='month_name',
            y='Sum',
            color='Department',
            category_orders={'month_name': month_order},
            labels={'Sum': 'Сумма (руб)', 'month_name': 'Месяц', 'Department': 'Отдел'},
            markers=True
        )

        # Линия тренда
        line_fig.add_trace(
            go.Scatter(
                x=dept_data['month_name'],
                y=dept_data.groupby('month_name')['Sum'].transform('mean'),
                name='Линия тренда',
                mode='lines+markers',
                line=dict(color='black', width=3, dash='dash'),
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


        # 2. Столбчатая диаграмма
        customer_data = filtered_df.groupby('Customer')['Sum'].sum().reset_index()
        bar_fig = px.bar(
            customer_data.sort_values('Sum', ascending=False),
            x='Customer',
            y='Sum',
            labels={'Sum': 'Сумма (руб)'}
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


        # 3. Круговая диаграмма
        pie_fig = px.pie(
            filtered_df.groupby('Responsible')['Sum'].sum().reset_index(),
            names='Responsible',
            values='Sum'
        )

        pie_fig.update_layout(
            legend_title_text='Ответственный',
            font=dict(family='Inter, sans-serif'),
            legend=dict(font=dict(size=st.GRAPH_FONT_SIZE)),
            paper_bgcolor=st.PAPER_BACKGROUND
        )

        
        # 4. Статистика
        def format_days(days):
            days = round(days)
            if days % 10 == 1 and days % 100 != 11:
                return f"{days} день"
            elif 2 <= days % 10 <= 4 and (days % 100 < 10 or days % 100 >= 20):
                return f"{days} дня"
            else:
                return f"{days} дней"

        def format_currency(amount):
            return f"{amount:,.0f}".replace(",", " ") + " ₽"

        stats = dbc.ListGroup([
            dbc.ListGroupItem(f'Количество счетов: {len(filtered_df)}'),
            dbc.ListGroupItem(f'Общая сумма: {format_currency(filtered_df["Sum"].sum())}'),
            dbc.ListGroupItem(f"Сумма неоплаченных счетов: {format_currency(filtered_df[filtered_df['Payment_date'].isna()]['Sum'].sum())}"),
            dbc.ListGroupItem(f'Медианное значение по сумме счёта: {format_currency(filtered_df["Sum"].median())}'),
            dbc.ListGroupItem(f'Среднее значение по сумме счёта: {format_currency(filtered_df["Sum"].mean())}'),
            dbc.ListGroupItem(f'Среднее время оплаты: {format_days(filtered_df["Payment_time"].mean())}'),
            dbc.ListGroupItem(f'Среднее значение по выполнению: {format_days(filtered_df["Exec_time"].mean())}'),
            
        ])
            


        return line_fig, bar_fig, pie_fig, stats