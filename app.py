from dash import Dash
import dash_bootstrap_components as dbc
from layouts import get_layouts
from callbacks import register_callbacks
# import psycopg2


app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])
app.layout = get_layouts()
register_callbacks(app)
server = app.server

if __name__ == "__main__":
    app.run(debug=True)