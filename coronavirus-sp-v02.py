
##########################################
#  1)  BIBLIOTECAS E INICIALIZAÇÕES      #
##########################################

import pandas               as pd
import streamlit            as st
import plotly.express       as px
from datetime import datetime, timedelta

st.set_page_config(layout='wide')

##########################################
#  2)  FUNÇÕES                           #
##########################################
# 2.1) Extração dos dados
@st.cache(allow_output_mutation = True)
def obtem_dados(url):
    df = pd.read_csv(url, sep=';', decimal=',')
    return df


# 2.2) Transformação dos dados
def organiza_datas(df):
    df['data'] = pd.to_datetime(df['datahora']).dt.strftime('%Y-%m-%d')
    df['mes-ano']    = pd.to_datetime(df['datahora']).dt.strftime('%Y-%m')
    df['semana-ano'] = pd.to_datetime(df['datahora']).dt.strftime('%Y-%W')


# 2.3) Total de casos e óbitos: Dados no ESP
@st.cache(allow_output_mutation = True)
def totais_esp(df):

    # -- Casos --
    # Novos casos por dia
    casos_novos_sp = df[['data', 'casos_novos']].groupby('data').sum().reset_index()
    casos_novos_sp.set_index('data', inplace=True)

    # Casos acumulados no ESP
    casos_acum_sp = casos_novos_sp.cumsum()

    # Médias Móveis de 7 dias para casos
    mm7d_casos = casos_novos_sp.rolling(window=7).mean()

    # Une dados sobre Casos
    casos_sp = pd.merge(casos_novos_sp, casos_acum_sp, how='left', left_index=True, right_index=True)
    casos_sp = pd.merge(casos_sp, mm7d_casos, how='left', left_index=True, right_index=True)
    casos_sp.columns = ['casos_novos', 'casos_acum', 'casos_mm7d']

    # Total de novos óbitos por dia no ESP
    obitos_novos_sp = dados_sp[['data', 'obitos_novos']].groupby('data').sum().reset_index()
    obitos_novos_sp.set_index('data', inplace=True)

    # Total de Óbitos acumulados no ESP
    obitos_acum_sp = obitos_novos_sp.cumsum()

    # Médias Móveis de 7 dias para óbitos
    mm7d_obitos = obitos_novos_sp.rolling(window=7).mean()

    # Une dados sobre Óbitos
    obitos_sp = pd.merge(obitos_novos_sp, obitos_acum_sp, how='left', left_index=True, right_index=True)
    obitos_sp = pd.merge(obitos_sp, mm7d_obitos, how='left', left_index=True, right_index=True)
    obitos_sp.columns = ['obitos_novos', 'obitos_acum', 'obitos_mm7d']

    return casos_sp, obitos_sp

def totais_municipio(df, municipio):
    # Casos
    casos_municipio = df.loc[df['nome_munic'] == municipio][['data', 'casos_novos']]
    casos_municipio.set_index('data', inplace=True)
    casos_municipio['casos_acum'] = casos_municipio['casos_novos'].cumsum()
    casos_municipio['casos_mm7d'] = casos_municipio['casos_novos'].rolling(window=7).mean()

    # Óbitos
    obitos_municipio = df.loc[df['nome_munic'] == municipio][['data', 'obitos_novos']]
    obitos_municipio.set_index('data', inplace=True)
    obitos_municipio['obitos_acum'] = obitos_municipio['obitos_novos'].cumsum()
    obitos_municipio['obitos_mm7d'] = obitos_municipio['obitos_novos'].rolling(window=7).mean()

    return casos_municipio, obitos_municipio


def ranking_municipios(df, populacao):

    # verifica opção mínima de população escolhida e filtra dataset
    if populacao == 'Todos':
        df2 = df.loc[df['pop'] > 0]
    elif populacao == '10 mil':
        df2 = df.loc[df['pop'] >= 10000]
    elif populacao == '20 mil':
        df2 = df.loc[df['pop'] >= 20000]
    elif populacao == '30 mil':
        df2 = df.loc[df['pop'] >= 30000]
    elif populacao == '50 mil':
        df2 = df.loc[df['pop'] >= 50000]
    elif populacao == '100 mil':
        df2 = df.loc[df['pop'] >= 100000]
    elif populacao == '200 mil':
        df2 = df.loc[df['pop'] >= 200000]
    elif populacao == '300 mil':
        df2 = df.loc[df['pop'] >= 300000]
    elif populacao == '500 mil':
        df2 = df.loc[df['pop'] >= 500000]
    else :
        df2 = df.loc[df['pop'] >= 1000000]

    return agrupa_dados(df2, 'nome_munic', 'Município')

def agrupa_dados(df, var_agrup, nome_agrup):
    # Última data no dataset
    data_0d = df['data'].max()
    data_0d = datetime.strptime(data_0d, '%Y-%m-%d').date()

    # Datas anteriores: 1 semana, 2 semanas, 1 mês
    data_7d  = str(data_0d - timedelta(days=7))
    data_14d = str(data_0d - timedelta(days=14))
    data_30d = str(data_0d - timedelta(days=30))
    data_0d  = str(data_0d)

    # Lista com datas que serão usadas
    filtro_datas = [data_0d, data_7d, data_14d, data_30d]

    # Filtra pelas datas
    rank = df[df['data'].isin(filtro_datas)]

    # Transpõe as data para as colunas
    rank = rank.pivot(index=[var_agrup, 'pop'], columns='data',
                                  values=['casos', 'obitos'])

    # Organiza e renomeia as colunas transpostas
    rank.columns = rank.columns.get_level_values(0)
    rank.columns = ['casos_30d' , 'casos_14d' , 'casos_7d' , 'casos_0d',
                    'obitos_30d', 'obitos_14d', 'obitos_7d', 'obitos_0d']

    # 'pop' deixa de ser index
    rank.reset_index(level=[var_agrup, 'pop'], inplace=True)

    # Taxas por 100 mil habitantes
    rank['taxa_casos']  = (rank['casos_0d']  / rank['pop']) * 100000
    rank['taxa_obitos'] = (rank['obitos_0d'] / rank['pop']) * 100000

    # Variações
    rank['casos_var_7d']   = rank['casos_0d']  / rank['casos_7d']   - 1
    rank['casos_var_14d']  = rank['casos_0d']  / rank['casos_14d']  - 1
    rank['casos_var_30d']  = rank['casos_0d']  / rank['casos_30d']  - 1
    rank['obitos_var_7d']  = rank['obitos_0d'] / rank['obitos_7d']  - 1
    rank['obitos_var_14d'] = rank['obitos_0d'] / rank['obitos_14d'] - 1
    rank['obitos_var_30d'] = rank['obitos_0d'] / rank['obitos_30d'] - 1

    # Ranking Casos
    rank_casos = rank.sort_values(by=['casos_0d', 'casos_7d', 'casos_14d', 'casos_30d'], ascending=False)
    rank_casos = rank_casos.reset_index(drop='index')

    # Ranking Óbitos
    rank_obitos = rank.sort_values(by=['obitos_0d', 'obitos_7d', 'obitos_14d', 'obitos_30d'], ascending=False)
    rank_obitos = rank_obitos.reset_index(drop='index')

    # Ranking Taxa de Casos
    rank_tx_casos = rank.sort_values(by=['taxa_casos', 'casos_0d', 'casos_7d', 'casos_14d', 'casos_30d', 'pop'], ascending=False)
    rank_tx_casos = rank_tx_casos.reset_index(drop='index')

    # Ranking Taxa de Óbitos
    rank_tx_obitos = rank.sort_values(by=['taxa_obitos', 'obitos_0d', 'obitos_7d', 'obitos_14d', 'obitos_30d', 'pop'], ascending=False)
    rank_tx_obitos = rank_tx_obitos.reset_index(drop='index')

    # Seleciona de colunas
    rank_casos = rank_casos[[var_agrup, 'pop', 'casos_0d', 'taxa_casos', 'casos_var_7d', 'casos_var_14d',
                             'casos_var_30d', 'obitos_0d', 'taxa_obitos']]

    rank_obitos = rank_obitos[[var_agrup, 'pop', 'obitos_0d', 'taxa_obitos', 'obitos_var_7d', 'obitos_var_14d',
                               'obitos_var_30d', 'casos_0d', 'taxa_casos']]

    rank_tx_casos = rank_tx_casos[[var_agrup, 'pop', 'taxa_casos', 'casos_0d', 'casos_var_7d', 'casos_var_14d',
                                   'casos_var_30d', 'obitos_0d', 'taxa_obitos']]

    rank_tx_obitos = rank_tx_obitos[[var_agrup, 'pop', 'taxa_obitos', 'obitos_0d', 'obitos_var_7d', 'obitos_var_14d',
                                     'obitos_var_30d', 'casos_0d', 'taxa_casos']]


    # Renomeia colunas
    rank_casos.columns = [nome_agrup, 'População', 'Casos', 'Taxa de Casos',
                          'Var. casos (7d)', 'Var. casos (14d)', 'Var. casos (em 30d)',
                          'Óbitos', 'Taxa de Óbitos']
    rank_tx_casos.columns = [nome_agrup, 'População', 'Taxa de Casos', 'Casos',
                             'Var. casos (7d)', 'Var. casos (14d)', 'Var. casos (em 30d)',
                             'Óbitos', 'Taxa de Óbitos']
    rank_obitos.columns = [nome_agrup, 'População', 'Óbitos', 'Taxa de Óbitos',
                          'Var. casos (7d)', 'Var. casos (14d)', 'Var. casos (em 30d)',
                          'Casos', 'Taxa de Casos']
    rank_tx_obitos.columns = [nome_agrup, 'População', 'Taxa de Óbitos', 'Óbitos',
                             'Var. casos (7d)', 'Var. casos (14d)', 'Var. casos (em 30d)',
                              'Casos', 'Taxa de Casos']

    return rank_casos, rank_obitos, rank_tx_casos, rank_tx_obitos



def graficos_casos_e_obitos(casos, obitos):

    c1, c2 = st.beta_columns(2)
    c1.subheader('Casos Novos por Dia')
    fig = px.line(casos, x=casos.index, y=['casos_novos','casos_mm7d'],
                  labels={'Casos Novos', 'Média Móvel se 7 dias'})
    fig.update_layout(xaxis_title='Datas', yaxis_title='Quantidade de Casos', legend_title='',
                      legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
    c1.plotly_chart(fig, use_container_width=True)

    c2.subheader('Casos Acumulados por Dia')
    fig = px.line(casos, x=casos.index, y='casos_acum')
    fig.update_layout(xaxis_title='Datas', yaxis_title='Casos Acumulados')
    c2.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.beta_columns(2)
    c1.subheader('Óbitos Novos por Dia')
    fig = px.line(obitos, x=obitos.index, y=['obitos_novos', 'obitos_mm7d'])
    fig.update_layout(xaxis_title='Datas', yaxis_title='Quantidade de Óbitos', legend_title='',
                      legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01))
    c1.plotly_chart(fig, use_container_width=True)

    c2.subheader('Óbitos Acumulados por Dia')
    fig = px.line(obitos, x=obitos.index, y='obitos_acum')
    fig.update_layout(xaxis_title='Datas', yaxis_title='Óbitos Acumulados')
    c2.plotly_chart(fig, use_container_width=True)


    return None

def totais_agrupamentos(dados, regioes, tipo_agrup):

    agrupados = pd.merge(dados, regioes, how='left', on='codigo_ibge')
    agrupados.fillna('Ignorado', inplace=True)

    if tipo_agrup == 'Regiões Administrativas':
        var = 'reg_adm'
        nome_var =  'Reg. Adm.'
    elif tipo_agrup == 'Regiões de Governo':
        var = 'reg_gov'
        nome_var = 'Reg. Gov.'
    elif tipo_agrup == 'Regiões Metropolitanas':
        var = 'reg_metrop'
        nome_var = 'Reg. Metrop.'
    elif tipo_agrup == 'Aglomerações Urbanas':
        var = 'aglom_urb'
        nome_var = 'Agl. Urb.'
    elif tipo_agrup == 'Departamento Regional de Saúde':
        var = 'drs'
        nome_var = 'DRS'
    elif tipo_agrup == 'Departamento Regional de Saúde - Plano São Paulo':
        var = 'drs_plano_sp'
        nome_var = 'DRS (Plano SP)'
    elif tipo_agrup == 'Regiões Administrativas Judiciárias (TJ-SP)':
        var = 'tj_raj'
        nome_var = 'RAJ (TJ-SP)'
    elif tipo_agrup == 'Circunscrições Judiciárias (TJ-SP)':
        var = 'tj_cj'
        nome_var = 'CJ (TJ-SP)'
    else: #'Comarcas (TJ-SP)'
        var = 'tj_comarca_2'
        nome_var = 'Comarca (TJ-SP)'

    agrupados = agrupados[[var, 'data', 'pop', 'casos', 'casos_novos', 'obitos', 'obitos_novos']].groupby([var, 'data']).sum().reset_index()

    agrupados = agrupados[agrupados['pop'] > 0]

    return agrupa_dados(agrupados, var, nome_var)


##########################################
#  3)  CÓDIGO                           #
##########################################

if __name__ == '__main__':

    st.title("Análise dos Dados sobre Coronavírus no Estado de São Paulo")

    # 3.1) Extração dos dados

    # 3.1.1) Dados do estado de São Paulo
    url = 'https://raw.githubusercontent.com/seade-R/dados-covid-sp/master/data/dados_covid_sp.csv'
    dados_sp = obtem_dados(url)
    # Exclusão da variável de Semana Epidemiológica
    #dados_sp.drop(['semana_epidem'], axis=1, inplace=True)

    # 3.1.2) Dados dos agrupamentos de municípios no estado de São Paulo
    url = 'https://raw.githubusercontent.com/diegofsfs/coronavirus-sp/main/regioes-sp.csv'
    agrupamentos_sp = obtem_dados(url)


    # 3.2) Transformação dos dados
    organiza_datas(dados_sp)

    # 3.3) Total de casos e óbitos: Dados no ESP
    st.header("Total de casos e óbitos no Estado de São Paulo")
    # Casos e óbitos (por dia, acumulado, média móvel dos últimos 7 dias)
    casos_sp, obitos_sp = totais_esp(dados_sp)

    # Filtros para gráficos
    ano_min = pd.to_datetime(casos_sp.index).min()
    ano_max = pd.to_datetime(casos_sp.index).max()

    #st.sidebar.title('Filtros dos gráficos')
    #st.sidebar.subheader('Filtre a data para os gráficos dos totais no Estado de São Paulo')

    # Filtro
    # NÃO FUNCIONA !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    #filtro_datas = st.sidebar.slider('Data Inicial', ano_min, ano_max, ano_min)
    #casos_sp = casos_sp.loc[casos_sp.index >= filtro_datas]
    #obitos_sp = obitos_sp.loc[obitos_sp.index >= filtro_datas]


    # Gráficos de casos e óbitos (novos casos + média móvel e casos acumulados)
    graficos_casos_e_obitos(casos_sp, obitos_sp)

    # 3.4) Ranking de casos, óbitos e respctivas taxas por Municípios
    st.header("Ranking dos municípios")
    st.write('Ao clicar no título de uma coluna os dados serão ordenados por essa variável')
    # Filtro população
    lista_populacao = ['Todos', '10 mil', '20 mil', '30 mil', '50 mil', '100 mil', '200 mil', '300 mil', '500 mil', '1 milhão']
    filtro_populacao = st.selectbox('População mínima dos municípios: ', lista_populacao)

    rank_casos, rank_obitos, rank_tx_casos, rank_tx_obitos = ranking_municipios(dados_sp, filtro_populacao)

    # Imprime datasets
    st.subheader('Ranking pelo total de casos')
    st.write(rank_casos)

    st.subheader('Ranking pelo total de óbitos')
    st.write(rank_obitos)

    st.text('Observação: "Var." representa a variação do indicador. ')
    st.text('Por exemplo, "Var. casos (7d)" representa a variação de casos em 7 dias a partir da última data disponível')

    # 3.5) Casos e Óbitos de um Município do Estado de São Paulo
    st.header("Total de casos e óbitos no município selecionado")

    # Seleção do nome do município
    filtro_municipio = st.selectbox('Selecione um município: ', sorted(set(dados_sp['nome_munic'].unique())))

    # Sumarizações dos dados do municípío
    casos_municipio, obitos_municipio = totais_municipio(dados_sp, filtro_municipio)

    # Gráficos de casos e óbitos no município
    graficos_casos_e_obitos(casos_municipio, obitos_municipio)



    # 3.6) Casos e Óbitos Agrupados por Regiões do Estado de São Paulo
    st.header("Total de casos e óbitos por agrupamentos de Municípios do Estado de São Paulo")

    # Opções de agrupamento
    lista_agrup = ['Regiões Administrativas',
                   'Regiões de Governo',
                   'Regiões Metropolitanas',
                   'Aglomerações Urbanas',
                   'Departamento Regional de Saúde',
                   'Departamento Regional de Saúde - Plano São Paulo',
                   'Regiões Administrativas Judiciárias (TJ-SP)',
                   'Circunscrições Judiciárias (TJ-SP)',
                   'Comarcas (TJ-SP)']
    filtro_agrup = st.selectbox('Selecione o tipo de agrupamento: ', lista_agrup)

    rank_ag_casos, rank_ag_obitos, rank_ag_tx_casos, rank_ag_tx_obitos = totais_agrupamentos(dados_sp, agrupamentos_sp, filtro_agrup)

    st.write('Ao clicar no título de uma coluna os dados serão ordenados por essa variável')

    st.subheader('Ranking pelo total de casos')
    st.write(rank_ag_casos)
    st.subheader('Ranking pelo total de óbitos')
    st.write(rank_ag_obitos)

    st.text('Observação: não foram considerados os municípios como "Ignorado" no agrupamento por regiões.')


    st.header('Fontes:')
    st.write('Dados sobre casos e óbitos por Coronavírus no Estado de São Paulo: [https://www.seade.gov.br/coronavirus/](https://www.seade.gov.br/coronavirus/)')
    st.write('Dados sobre agrupamentos de municípios no Estado de São Paulo (exceto regiões do TJ-SP): [http://produtos.seade.gov.br/produtos/divpolitica/](http://produtos.seade.gov.br/produtos/divpolitica/)')
    st.write('Dados sobre agrupamentos de municípios pelas regiões do TJ-SP: através de consulta pelo SIC do TJ-SP, número 2020/00055867')
    st.write('Divisões do Plano São Paulo: [https://www.seade.gov.br/wp-content/uploads/2021/02/Boletim-Coronavirus-Anexo-metodologico.pdf](https://www.seade.gov.br/wp-content/uploads/2021/02/Boletim-Coronavirus-Anexo-metodologico.pdf)')

    st.header('Criação:')
    st.write('Está página foi criada por Diego Ferreira Schiezari')
    st.write('Para dúvidas, sugestões, críticas ou contato profissional, veja as opções abaixo')
    st.markdown('E-mail: <a href="mailto:diegofsfs@gmail.com">diegofsfs@gmail.com</a>', unsafe_allow_html=True)
    st.write('Linkedin: [https://www.linkedin.com/in/diegofsfs](https://www.linkedin.com/in/diegofsfs)')
    st.write('Github: [https://github.com/diegofsfs](https://github.com/diegofsfs)')

    #st.write("check out this [link](https://share.streamlit.io/mesmith027/streamlit_webapps/main/MC_pi/streamlit_app.py)")

    #########
    # FALTA #
    #########

    # 3.3) Slider para filtrar o período

    # 3.4) Seleção da variável que será ordenada (não dá para fazer no próprio Chrome)
