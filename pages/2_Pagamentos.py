import streamlit as st
import pandas as pd
import plotly.express as px
import textwrap

# Configuração da página
st.set_page_config(page_title="Dashboard de Pagamentos", layout="wide")
st.title("📊 Dashboard de Pagamentos de Incentivo")

MESES_MAP = {
    '01': '01 - Janeiro', '02': '02 - Fevereiro', '03': '03 - Março',
    '04': '04 - Abril', '05': '05 - Maio', '06': '06 - Junho',
    '07': '07 - Julho', '08': '08 - Agosto', '09': '09 - Setembro',
    '10': '10 - Outubro', '11': '11 - Novembro', '12': '12 - Dezembro'
}

@st.cache_data
def load_data(file):
    # O Pandas consegue ler diretamente o arquivo carregado pelo Streamlit
    df = pd.read_excel(file, header=1)
    
    df['Descrição de situação da parcela'] = df['Descrição de situação da parcela'].fillna('-')
    df['Detalhes do processamento da parcela'] = df['Detalhes do processamento da parcela'].fillna('-')
    
    df['Periodo_Str'] = df['Período de referência'].dropna().astype(int).astype(str)
    
    df['Ano'] = df['Periodo_Str'].str[:4]
    df['Mes_Num'] = df['Periodo_Str'].str[4:6]
    
    df['Mês'] = df['Mes_Num'].map(MESES_MAP).fillna(df['Mes_Num'])
    df['Período Formatado'] = df['Mes_Num'] + "/" + df['Ano']
    
    return df

# ==========================
# UPLOAD DE ARQUIVO
# ==========================
st.sidebar.header("📂 Base de Dados")
arquivo_carregado = st.sidebar.file_uploader("Faça o upload da planilha EMR (.xlsx)", type=["xlsx"])

# Se nenhum arquivo foi carregado, exibe uma mensagem e interrompe a execução do resto do código
if arquivo_carregado is None:
    st.info("👋 Olá! Para começar, arraste a sua planilha de pagamentos para o menu lateral ou clique em 'Browse files'.")
    st.stop()

# Carrega os dados do arquivo enviado
try:
    df = load_data(arquivo_carregado)
except Exception as e:
    st.error(f"Erro ao ler o arquivo. Verifique se é a planilha padrão do SGP. Detalhes: {e}")
    st.stop()

# ==========================
# BARRA LATERAL (FILTROS)
# ==========================
st.sidebar.markdown("---")
st.sidebar.header("🔍 Filtros de Busca")
st.sidebar.markdown("Selecione as opções abaixo. Os filtros funcionam em cascata.")

df_filtrado = df.copy()

unidades = sorted(df_filtrado['Nome da Unidade de Ensino'].dropna().unique().tolist())
unidade_selecionada = st.sidebar.multiselect("🏫 Selecione o(s) Campus:", options=unidades, default=[])
if unidade_selecionada:
    df_filtrado = df_filtrado[df_filtrado['Nome da Unidade de Ensino'].isin(unidade_selecionada)]

anos = sorted(df_filtrado['Ano'].dropna().unique().tolist())
ano_selecionado = st.sidebar.multiselect("📅 Ano de Referência:", options=anos, default=[])
if ano_selecionado:
    df_filtrado = df_filtrado[df_filtrado['Ano'].isin(ano_selecionado)]

meses = sorted(df_filtrado['Mês'].dropna().unique().tolist())
mes_selecionado = st.sidebar.multiselect("📅 Mês de Referência:", options=meses, default=[])
if mes_selecionado:
    df_filtrado = df_filtrado[df_filtrado['Mês'].isin(mes_selecionado)]

tipos = sorted(df_filtrado['Tipo de incentivo'].dropna().unique().tolist())
tipo_selecionado = st.sidebar.multiselect("🏷️ Tipo de Incentivo:", options=tipos, default=[])
if tipo_selecionado:
    df_filtrado = df_filtrado[df_filtrado['Tipo de incentivo'].isin(tipo_selecionado)]

status_list = sorted(df_filtrado['Status'].dropna().unique().tolist())
status_selecionado = st.sidebar.multiselect("💳 Situação de Pagamento:", options=status_list, default=[])
if status_selecionado:
    df_filtrado = df_filtrado[df_filtrado['Status'].isin(status_selecionado)]

estudantes_list = sorted(df_filtrado['Nome'].dropna().unique().tolist())
estudante_selecionado = st.sidebar.multiselect("🎓 Selecione o Estudante (Opcional):", options=estudantes_list, default=[])
if estudante_selecionado:
    df_filtrado = df_filtrado[df_filtrado['Nome'].isin(estudante_selecionado)]

# ==========================
# DETALHAMENTO DO ESTUDANTE
# ==========================
if estudante_selecionado:
    st.subheader("👤 Detalhamento de Parcelas do Estudante")
    
    colunas_exibicao = [
        'Nome', 'Período Formatado', 'Tipo de incentivo', 
        'Status', 'Valor do incentivo', 'Descrição de situação da parcela'
    ]
    
    df_detalhe = df_filtrado.sort_values(by=['Nome', 'Período de referência']).copy()
    
    df_detalhe['Valor do incentivo'] = df_detalhe['Valor do incentivo'].apply(
        lambda x: f"R$ {float(x):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    
    st.table(df_detalhe[colunas_exibicao].set_index('Nome'))
    st.markdown("---")

# ==========================
# MÉTRICAS PRINCIPAIS (KPIs)
# ==========================
st.subheader("📈 Resumo dos Filtros Aplicados" if len(df_filtrado) < len(df) else "📈 Resumo Geral da Rede")
col1, col2, col3, col4 = st.columns(4)

volume_pago = df_filtrado[df_filtrado['Status'] == 'Pago']['Valor do incentivo'].sum()
total_incentivos = len(df_filtrado)
total_alunos = df_filtrado['CPF'].nunique()
bloqueados = len(df_filtrado[df_filtrado['Status'] == 'Bloqueado'])

col1.metric("Volume Total Pago", f"R$ {volume_pago:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col2.metric("Total de Estudantes", total_alunos)
col3.metric("Parcelas Processadas", total_incentivos)
col4.metric("Parcelas Bloqueadas", bloqueados)

st.markdown("---")

# ==========================
# GRÁFICOS DE ANÁLISE
# ==========================
if not df_filtrado.empty:
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.markdown("#### Situação Geral das Parcelas")
        status_counts = df_filtrado['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Quantidade']
        fig_status = px.pie(status_counts, values='Quantidade', names='Status', hole=0.4, 
                            color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_status, use_container_width=True)

    with col_graf2:
        st.markdown("#### Volume Pago por Tipo de Incentivo")
        df_pago = df_filtrado[df_filtrado['Status'] == 'Pago']
        if not df_pago.empty:
            vol_por_tipo = df_pago.groupby('Tipo de incentivo')['Valor do incentivo'].sum().reset_index()
            fig_tipo = px.bar(vol_por_tipo, x='Tipo de incentivo', y='Valor do incentivo', 
                              text_auto='.2s', color='Tipo de incentivo',
                              color_discrete_sequence=px.colors.qualitative.Set2)
            st.plotly_chart(fig_tipo, use_container_width=True)
        else:
            st.info("Nenhum valor pago correspondente aos filtros atuais.")

    st.markdown("#### Motivos e Detalhamento da Situação (Visão Geral)")
    sit_counts = df_filtrado['Descrição de situação da parcela'].value_counts().reset_index()
    sit_counts.columns = ['Descrição Completa', 'Quantidade']

    sit_counts['Motivo (Resumo)'] = sit_counts['Descrição Completa'].apply(
        lambda x: str(x)[:70] + '...' if len(str(x)) > 70 else str(x)
    )

    sit_counts['Descrição Completa'] = sit_counts['Descrição Completa'].apply(
        lambda x: "<br>".join(textwrap.wrap(str(x), width=80))
    )

    fig_sit = px.bar(sit_counts, y='Motivo (Resumo)', x='Quantidade', 
                     orientation='h', color='Quantidade', 
                     color_continuous_scale='Blues',
                     hover_data={'Descrição Completa': True, 'Motivo (Resumo)': False})
    
    altura_dinamica = max(400, len(sit_counts) * 45)
    
    fig_sit.update_layout(
        yaxis={'categoryorder':'total ascending'},
        height=altura_dinamica
    )
    st.plotly_chart(fig_sit, use_container_width=True)
else:
    st.warning("Nenhum dado encontrado para os filtros selecionados. Tente limpar os filtros na barra lateral.")

# ==========================
# TABELA DE DETALHAMENTO (LISTA DE ALUNOS)
# ==========================
st.markdown("---")
st.subheader("📋 Detalhamento dos Estudantes")

if not df_filtrado.empty:
    st.write(f"A apresentar **{len(df_filtrado)}** registo(s) com base nos filtros selecionados.")
    
    # Vamos definir as colunas mais importantes para não poluir a visualização.
    # Pode adicionar ou remover colunas desta lista conforme os nomes exatos que estão na sua planilha.
    colunas_desejadas = [
        'Nome', 
        'CPF', 
        'Nome da Unidade de Ensino', 
        'Tipo de incentivo', 
        'Situação', 
        'Descrição da parcela'
    ]
    
    # Garante que apenas colunas que realmente existem na planilha serão exibidas, evitando erros
    colunas_exibicao = [col for col in colunas_desejadas if col in df_filtrado.columns]
    
    # Se por acaso nenhuma das colunas acima existir, mostra todas as colunas
    if not colunas_exibicao:
        colunas_exibicao = df_filtrado.columns.tolist()
        
    df_tabela = df_filtrado[colunas_exibicao].copy()
    
    # Exibe a tabela interativa (ocultando o índice numérico lateral para ficar mais limpo)
    st.dataframe(df_tabela, use_container_width=True, hide_index=True)
else:
    st.info("Nenhum estudante encontrado com os filtros atuais.")