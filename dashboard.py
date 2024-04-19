import pandas as pd
import geopandas as gpd
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Load station data
stations_df = pd.read_csv('final_data/full_stations_metadata.csv')

# Load temperature data
temps_df = pd.read_csv('final_data/donnesIN.csv')

# Preprocess data
# Merge station data with temperature data
data = pd.merge(stations_df, temps_df, on='NUM_POST')

# Calculate yearly mean temperature for each department
data_fr_map = data.copy()
data_fr_map['YYYYMM'] = data_fr_map['YYYYMM'].astype(str).str[:4]
dept_temps = data_fr_map.groupby(['num_dep', 'YYYYMM'])['VALEUR'].mean().reset_index()

# Load French departments boundaries using geopandas
france_departments = gpd.read_file('france_departements.geojson')
france_departments['code'] = france_departments['code'].astype(int)

# Merge temperature data with department boundaries
dept_temps_geo = pd.merge(dept_temps, france_departments,
                          how='left', left_on='num_dep', right_on='code')

# Create Dash app
app = dash.Dash(__name__)

# Define layout
app.layout = html.Div([
    html.H1("French Weather Dashboard"),
    dcc.Graph(id='station-map'),
    dcc.Graph(id='dept-temperature-map'),
    dcc.Slider(
        id='year-slider',
        min=int(dept_temps['YYYYMM'].min()),
        max=int(dept_temps['YYYYMM'].max()),
        value=int(dept_temps['YYYYMM'].min()),
        marks={str(year): str(year) for year in dept_temps['YYYYMM'].unique()},
        step=None
    )
])

# Define callbacks
@app.callback(
    [Output('dept-temperature-map', 'figure')],
    [Input('year-slider', 'value')]
)
def update_dept_map(selected_year):
    # Filter data for the selected year
    dept_data = dept_temps_geo[dept_temps_geo['YYYYMM'] == str(selected_year)]
    # Create chloropleth map
    dept_map = px.choropleth(dept_data, geojson=dept_data.geometry, locations=dept_data.num_dep,
                              color='VALEUR', scope="europe",
                              labels={'temperature': 'Mean Temperature (°C)'})
    return [dept_map]


if __name__ == '__main__':
    app.run_server(debug=True)