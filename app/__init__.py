rom flask import Flask
from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px

# Carregar dados
data = pd.read_excel('Dados_coordenada_V3 (1).xlsx')

# Configuração do Flask
server = Flask(__name__)

# Inicialização do Dash
app = Dash(__name__, server=server, url_base_pathname='/dashboard/')

# Layout do Dash
app.layout = html.Div([
    html.H1("Métricas Avançadas"),
    
    # Filtros
    html.Div([
        dcc.Dropdown(
            id='year-filter',
            options=[{'label': str(y), 'value': y} for y in sorted(data['Year'].unique())],
            value=sorted(data['Year'].unique())[0],
            placeholder='Selecione um ano'
        ),
        dcc.Dropdown(
            id='country-filter',
            options=[{'label': c, 'value': c} for c in data['Country'].unique()],
            value=data['Country'].unique()[0],
            placeholder='Selecione um país',
            style={'width': '300px', 'height': '50px', 'font-size': '16px'}

        ),
        dcc.Dropdown(
            id='segmentation-filter',
            options=[{'label': s, 'value': s} for s in data['Segmentation'].unique()],
            value=data['Segmentation'].unique()[0],
            placeholder='Selecione uma segmentação',
            style={'width': '300px', 'height': '50px', 'font-size': '16px'}
        ),
    ], style={'display': 'flex', 'gap': '20px', 'align-items': 'center'}),
    
    # Gráficos
    dcc.Tabs([
        dcc.Tab(label='Volume Total', children=[
            dcc.Graph(id='volume-graph')
        ]),
        dcc.Tab(label='Crescimento Temporal', children=[
            dcc.Graph(id='growth-graph')
        ]),
        dcc.Tab(label='Participação de Mercado', children=[
            dcc.Graph(id='market-share-graph')
        ]),
        dcc.Tab(label='Mapa Geográfico', children=[
            dcc.Graph(id='geo-map')
        ]),
        dcc.Tab(label='Top Marcas por Volume', children=[
            dcc.Graph(id='top-brands-graph')
        ]),
        dcc.Tab(label='Classificação Premium', children=[
            dcc.Graph(id='premium-graph')
        ])
    ])
])

# Callbacks para gráficos
@app.callback(
    Output('volume-graph', 'figure'),
    [Input('year-filter', 'value'), Input('country-filter', 'value'), Input('segmentation-filter', 'value')]
)
def update_volume_graph(selected_year, selected_country, selected_segmentation):
    filtered_data = data[
        (data['Year'] == selected_year) &
        (data['Country'] == selected_country) &
        (data['Segmentation'] == selected_segmentation)
    ]
    fig = px.bar(filtered_data, x='Brand', y='Box 9L', color='Brand',
                 title=f'Volume de Vendas ({selected_year}, {selected_country}, {selected_segmentation})')
    return fig

@app_dash.callback(
    Output('growth-graph', 'figure'),
    [Input('year-filter', 'value'), Input('country-filter', 'value')]
)
def update_growth_graph(selected_year, selected_country):
    # Garantir que os tipos de dados estejam corretos
    selected_year = str(selected_year)
    selected_country = str(selected_country)

    # Filtrar os dados corretamente
    filtered_data = data.loc[
        (data['Year'] == int(selected_year)) & 
        (data['Country'].str.strip().str.lower() == selected_country.strip().lower())
    ].copy()  # Use .copy() para evitar o SettingWithCopyWarning

    if filtered_data.empty:
        return px.line(title=f"Sem dados disponíveis para 'Crescimento Temporal' ({selected_country}, {selected_year}).")

    # Garantir que 'Box 9L' seja numérico e modificar de forma segura
    filtered_data['Box 9L'] = pd.to_numeric(filtered_data['Box 9L'], errors='coerce')

    # Preencher valores nulos com zero
    filtered_data['Box 9L'] = filtered_data['Box 9L'].fillna(0)

    # Agrupar os dados e garantir que 'Box 9L' seja numérico
    grouped_data = filtered_data.groupby(['Month']).sum().reset_index()
    grouped_data['Box 9L'] = pd.to_numeric(grouped_data['Box 9L'], errors='coerce')

    grouped_data['Month'] = pd.to_datetime(grouped_data['Month'], format='%m').dt.strftime('%b')

    fig = px.line(
        grouped_data, x='Month', y='Box 9L', 
        title=f'Crescimento Temporal ({selected_country}, {selected_year})',
        markers=True
    )
    return fig


@app.callback(
    Output('market-share-graph', 'figure'),
    [Input('year-filter', 'value'), Input('country-filter', 'value')]
)
def update_market_share_graph(selected_year, selected_country):
    # Garantir que os tipos de dados estejam corretos
    selected_year = str(selected_year)
    selected_country = str(selected_country)

    # Filtrar os dados corretamente
    filtered_data = data.loc[
        (data['Year'] == int(selected_year)) & 
        (data['Country'].str.strip().str.lower() == selected_country.strip().lower())
    ].copy()  # Use .copy() para evitar o SettingWithCopyWarning

    if filtered_data.empty:
        return px.pie(title=f"Sem dados disponíveis para 'Participação de Mercado' ({selected_country}, {selected_year}).")

    # Garantir que 'Box 9L' seja numérico
    filtered_data['Box 9L'] = pd.to_numeric(filtered_data['Box 9L'], errors='coerce')

    if 'Segmentation' not in data.columns or 'Box 9L' not in data.columns:
        return px.pie(title="Erro: Colunas necessárias não encontradas.")

    grouped_data = filtered_data.groupby('Segmentation').sum().reset_index()

    if grouped_data.empty:
        return px.pie(title="Sem dados suficientes para 'Participação de Mercado'.")

    grouped_data['Box 9L'] = pd.to_numeric(grouped_data['Box 9L'], errors='coerce')

    fig = px.pie(
        grouped_data, names='Segmentation', values='Box 9L', 
        title=f'Participação de Mercado ({selected_country}, {selected_year})'
    )
    return fig


@app.callback(
    Output('top-brands-graph', 'figure'),
    [Input('year-filter', 'value'), Input('country-filter', 'value')]
)
def update_top_brands_graph(selected_year, selected_country):
    # Filtrar os dados corretamente
    filtered_data = data.loc[
        (data['Year'] == int(selected_year)) & 
        (data['Country'].str.strip().str.lower() == selected_country.strip().lower())
    ].copy()  # Use .copy() para evitar o SettingWithCopyWarning

    # Validar dados e colunas
    if filtered_data.empty or 'Brand' not in data.columns or 'Box 9L' not in data.columns:
        return px.bar(title="Sem dados disponíveis para 'Top Marcas por Volume'.")

    # Agrupamento e gráfico
    grouped_data = (
        filtered_data.groupby('Brand')
        .sum()
        .reset_index()
        .sort_values('Box 9L', ascending=False)
        .head(10)
    )
    if grouped_data.empty:
        return px.bar(title="Dados insuficientes para gerar o gráfico de 'Top Marcas'.")

    fig = px.bar(
        grouped_data, x='Brand', y='Box 9L', color='Brand', 
        title=f'Top 10 Marcas por Volume ({selected_country}, {selected_year})'
    )
    return fig

@app.callback(
    Output('premium-graph', 'figure'),
    [Input('year-filter', 'value'), Input('country-filter', 'value')]
)
def update_premium_graph(selected_year, selected_country):
    # Garantir que os tipos de dados estejam corretos
    selected_year = str(selected_year)
    selected_country = str(selected_country)

    # Filtrar os dados corretamente e criar uma cópia para evitar SettingWithCopyWarning
    filtered_data = data.loc[
        (data['Year'] == int(selected_year)) & 
        (data['Country'].str.strip().str.lower() == selected_country.strip().lower())
    ].copy()

    # Validar se os dados ou colunas necessárias estão disponíveis
    if filtered_data.empty or 'Segmentation' not in data.columns or 'Box 9L' not in data.columns:
        return px.bar(title="Sem dados disponíveis para 'Classificação Premium'.")

    # Agrupar dados por segmentação e calcular os valores totais
    grouped_data = filtered_data.groupby('Segmentation').sum().reset_index()

    # Verificar se o agrupamento resultou em dados válidos
    if grouped_data.empty:
        return px.bar(title="Dados insuficientes para gerar o gráfico de 'Classificação Premium'.")

    # Criar o gráfico
    fig = px.bar(
        grouped_data, 
        x='Segmentation', 
        y='Box 9L', 
        color='Segmentation',
        title=f'Classificação Premium ({selected_country}, {selected_year})',
        labels={'Box 9L': 'Volume de Vendas', 'Segmentation': 'Classificação'}
    )
    return fig

@app.callback(
    Output('geo-map', 'figure'),
    [Input('year-filter', 'value'), Input('country-filter', 'value')]
)
def update_geo_map(selected_year, selected_country):
    filtered_data = data[(data['Year'] == selected_year) & (data['Country'] == selected_country)]
    
    # Criar o gráfico de dispersão
    fig = px.scatter_mapbox(
        filtered_data, lat='Latitude', lon='Longitude', size='Box 9L', color='Brand',
        mapbox_style='open-street-map', zoom=6, title=f'Concentração de Vendas ({selected_country}, {selected_year})'
    )
    
    # Ajuste o tamanho máximo das bolinhas de dispersão
    fig.update_traces(marker=dict(
        sizemode='area',
        sizeref=2.*max(filtered_data['Box 9L'])/(100.**2),  # Ajuste o fator para controlar o tamanho
        size=filtered_data['Box 9L']
    ))

    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    return fig

    
# Rota principal no Flask
@app.route('/')
def index():
    return "Bem-vindo ao Dashboard! Acesse /dashboard para visualizar os gráficos."

# Executar o servidor
if __name__ == '__main__':
    app.run( )
