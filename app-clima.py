import pandas as pd
import streamlit as st
import requests
from io import BytesIO
from datetime import datetime, timedelta
from streamlit_js_eval import streamlit_js_eval  # Importação do streamlit-js-eval

# URL da logo do LAMMA para cabeçalho do app
LOGO_LAMMA_URL_HEADER = "https://lamma.com.br/wp-content/uploads/2024/08/lammapy-removebg-preview.png"

# URL da imagem do NASA POWER para a barra lateral
LOGO_NASA_POWER_URL_SIDEBAR = "https://www.earthdata.nasa.gov/s3fs-public/styles/small_third_320px_/public/2022-11/power_logo_event.png?VersionId=pZIOrAAZH6vCGOJMjhhwP91WJkg0sCus&itok=DrjfYom6"

# Função para buscar dados da API NASA POWER
def obter_dados_nasa(latitude, longitude, data_inicio, data_fim):
    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR,RH2M,T2M,T2M_MAX,T2M_MIN,T2MDEW,WS2M,WS2M_MAX,WS2M_MIN,ALLSKY_SFC_SW_DWN,CLRSKY_SFC_SW_DWN&community=RE&longitude={longitude}&latitude={latitude}&start={data_inicio}&end={data_fim}&format=JSON"
    
    response = requests.get(url)
    if response.status_code == 200:
        dados = response.json()
        # Organizando os dados que vêm da API
        parametros = dados['properties']['parameter']
        df = pd.DataFrame({
            'Data': list(parametros['T2M'].keys()),
            'P': parametros['PRECTOTCORR'].values(),  # Precipitação
            'UR': parametros['RH2M'].values(),        # Umidade Relativa
            'Tmed': parametros['T2M'].values(),       # Temperatura Média
            'Tmax': parametros['T2M_MAX'].values(),   # Temperatura Máxima
            'Tmin': parametros['T2M_MIN'].values(),   # Temperatura Mínima
            'Tdew': parametros['T2MDEW'].values(),    # Ponto de Orvalho
            'U2': parametros['WS2M'].values(),        # Velocidade do Vento a 2m
            'U2max': parametros['WS2M_MAX'].values(), # Velocidade Máxima do Vento a 2m
            'U2min': parametros['WS2M_MIN'].values(), # Velocidade Mínima do Vento a 2m
            'Qg': parametros['ALLSKY_SFC_SW_DWN'].values(), # Radiação Solar Incidente
            'Qo': parametros['CLRSKY_SFC_SW_DWN'].values()  # Radiação Solar na Superfície
        })
        return df
    else:
        return None

# Função para obter a geolocalização do usuário via navegador
def obter_localizacao_navegador():
    loc = streamlit_js_eval(js_expressions="navigator.geolocation.getCurrentPosition((pos) => {return {latitude: pos.coords.latitude, longitude: pos.coords.longitude}})", key="loc")
    return loc

# Interface do Streamlit
# Adiciona a logo do LAMMA no topo do app
st.image(LOGO_LAMMA_URL_HEADER, use_column_width=True)

# Informações sobre o laboratório
st.subheader("Aplicativo desenvolvido pelo LAMMA - Laboratório de Máquinas e Mecanização Agrícola da UNESP/Jaboticabal")

st.title("NASA POWER - Download de Dados Climáticos")

# Barra lateral com informações e explicações
st.sidebar.title("Informações sobre o App")
st.sidebar.image(LOGO_NASA_POWER_URL_SIDEBAR, use_column_width=True)

st.sidebar.write("""
### Importância dos Dados Climáticos:
- Os dados climáticos são fundamentais para o planejamento agrícola, monitoramento ambiental e gestão de recursos naturais.
- O acesso a informações sobre temperatura, precipitação, umidade e radiação solar ajuda a entender padrões climáticos e otimizar atividades no campo.

### Objetivo do Aplicativo:
- Este aplicativo oferece uma maneira simples e prática de obter dados climáticos de qualquer local do mundo, utilizando as coordenadas geográficas e o período selecionado pelo usuário.
- O aplicativo permite baixar os dados diretamente em formato Excel, facilitando a análise e integração com outros sistemas.

### Sobre o NASA POWER:
- O **NASA POWER** (Prediction of Worldwide Energy Resources) é um sistema que fornece dados climáticos históricos e atuais a partir de satélites da NASA.
""")

# Botão para usar localização atual do usuário, acima dos campos de coordenadas
if st.button("Usar minha localização"):
    localizacao = obter_localizacao_navegador()
    if localizacao:
        st.session_state['latitude'] = localizacao["latitude"]
        st.session_state['longitude'] = localizacao["longitude"]
        st.success(f"Localização definida: Latitude {localizacao['latitude']}, Longitude {localizacao['longitude']}")
    else:
        st.error("Não foi possível obter a localização.")

# Inputs para latitude e longitude
latitude = st.number_input("Latitude", format="%.6f", value=st.session_state.get('latitude', -21.7946))
longitude = st.number_input("Longitude", format="%.6f", value=st.session_state.get('longitude', -48.1766))

# Definindo o intervalo de datas: máximo de 30 anos atrás e a data de fim como a data atual
hoje = datetime.today()
trinta_anos_atras = hoje - timedelta(days=30 * 365)

data_inicio = st.date_input("Data de início", value=trinta_anos_atras, min_value=datetime(1990, 1, 1), max_value=hoje)
data_fim = st.date_input("Data de fim", value=hoje, min_value=data_inicio, max_value=hoje)

# Converter as datas para o formato YYYYMMDD exigido pela API
data_inicio_formatada = data_inicio.strftime("%Y%m%d")
data_fim_formatada = data_fim.strftime("%Y%m%d")

# Botão para buscar dados
if st.button("Buscar dados"):
    st.session_state['dados'] = obter_dados_nasa(latitude, longitude, data_inicio_formatada, data_fim_formatada)
    
    if st.session_state['dados'] is not None:
        st.success("Dados obtidos com sucesso!")
        st.write(st.session_state['dados'])
        
        # Permitir download dos dados em formato Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            st.session_state['dados'].to_excel(writer, sheet_name="Dados_Climaticos", index=False)
        output.seek(0)

        st.download_button(
            label="Baixar dados como Excel",
            data=output,
            file_name="dados_climaticos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Erro ao buscar dados da NASA POWER")
