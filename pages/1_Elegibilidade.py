import streamlit as st
import pandas as pd
import plotly.express as px
import textwrap
import ast

# Configuração da página
st.set_page_config(page_title="Dashboard de Elegibilidade", layout="wide")
st.title("🎯 Dashboard de Elegibilidade - Pé-de-Meia")

# Dicionário do INEP para Etapas de Ensino Médio/Técnico
ETAPAS_MAP = {
    '25': '25 - 1ª Série (Ensino Médio Regular)',
    '26': '26 - 2ª Série (Ensino Médio Regular)',
    '27': '27 - 3ª Série (Ensino Médio Regular)',
    '28': '28 - 4ª Série (Ensino Médio Regular)',
    '30': '30 - 1ª Série (Ensino Médio Integrado)',
    '31': '31 - 2ª Série (Ensino Médio Integrado)',
    '32': '32 - 3ª Série (Ensino Médio Integrado)',
    '33': '33 - 4ª Série (Ensino Médio Integrado)'
}

def formatar_cpf(cpf):
    if pd.isna(cpf) or str(cpf).strip() in ['', 'nan', '0.0']:
        return "-"
    cpf_str = str(int(float(cpf))).zfill(11)
    return f"{cpf_str[:3]}.{cpf_str[3:6]}.{cpf_str[6:9]}-{cpf_str[9:]}"

def formatar_nis(nis):
    if pd.isna(nis) or str(nis).strip() in ['', 'nan', '0.0']:
        return "-"
    nis_str = str(int(float(nis))).zfill(11)
    return f"{nis_str[:3]}.{nis_str[3:8]}.{nis_str[8:10]}-{nis_str[10:]}"

def extrair_motivos(detalhamento_str):
    if pd.isna(detalhamento_str) or str(detalhamento_str).strip() in ['', '-']:
        return []
    try:
        lista_motivos = ast.literal_eval(str(detalhamento_str))
        if isinstance(lista_motivos, list):
            return [item.get('nome', 'Motivo Desconhecido') for item in lista_motivos if 'nome' in item]
    except:
        pass
    return []

@st.cache_data
def load_data(file):
    df = pd.read_excel(file, header=1)
    
    df['Descrição'] = df['Descrição'].fillna('-')
    df['Detalhamento'] = df['Detalhamento'].fillna('-')
    
    df['CPF Formatado'] = df['CPF'].apply(formatar_cpf)
    df['NIS Formatado'] = df['NIS'].apply(formatar_nis)
    
    df['Código Etapa Ensino'] = df['Código Etapa Ensino'].fillna(0).astype(int).astype(str)
    
    # Criamos uma coluna puramente para ordenar internamente (25, 26, 30, 31...)
    df['Ordem_Etapa'] = df['Código Etapa Ensino'].astype(int)
    
    df['Etapa de Ensino (Traduzida)'] = df['Código Etapa Ensino'].map(ETAPAS_MAP).fillna(df['Código Etapa Ensino'] + ' - Outra Etapa')
    
    df['Lista_Motivos'] = df['Detalhamento'].apply(extrair_motivos)
    df['Motivos_Formatados'] = df['Lista_Motivos'].apply(
        lambda x: " | ".join(x) if len(x) > 0 else "Sem pendências"
    )
    
    return df

# ==========================
# UPLOAD DE ARQUIVO
# ==========================
st.sidebar.header("📂 Base de Dados")
arquivo_carregado = st.sidebar.file_uploader("Faça o upload da planilha de Elegibilidade (.xlsx)", type=["xlsx"])

if arquivo_carregado is None:
    st.info("👋 Bem-vindo à página de Elegibilidade! Arraste a sua planilha de elegibilidade para o menu lateral para iniciar.")
    st.stop()

try:
    df = load_data(arquivo_carregado)
except Exception as e:
    st.error(f"Erro ao ler o arquivo. Detalhes: {e}")
    st.stop()

# ==========================
# BARRA LATERAL (FILTROS)
# ==========================
st.sidebar.markdown("---")
st.sidebar.header("🔍 Filtros de Busca")

df_filtrado = df.copy()

unidades = sorted(df_filtrado['Nome da Unidade de Ensino'].dropna().unique().tolist())
unidade_selecionada = st.sidebar.multiselect("🏫 Selecione o(s) Campus:", options=unidades, default=[])
if unidade_selecionada:
    df_filtrado = df_filtrado[df_filtrado['Nome da Unidade de Ensino'].isin(unidade_selecionada)]

situacoes = sorted(df_filtrado['Situação'].dropna().unique().tolist())
situacao_selecionada = st.sidebar.multiselect("🎯 Situação:", options=situacoes, default=[])
if situacao_selecionada:
    df_filtrado = df_filtrado[df_filtrado['Situação'].isin(situacao_selecionada)]

# Filtro lateral já ordenado usando o código INEP
etapas = df_filtrado[['Ordem_Etapa', 'Etapa de Ensino (Traduzida)']].drop_duplicates().sort_values(by='Ordem_Etapa')['Etapa de Ensino (Traduzida)'].tolist()
etapa_selecionada = st.sidebar.multiselect("📚 Etapa de Ensino:", options=etapas, default=[])
if etapa_selecionada:
    df_filtrado = df_filtrado[df_filtrado['Etapa de Ensino (Traduzida)'].isin(etapa_selecionada)]

todos_motivos_listas = df_filtrado[df_filtrado['Situação'] != 'Elegível']['Lista_Motivos'].tolist()
motivos_unicos = sorted(list(set([motivo for sublista in todos_motivos_listas for motivo in sublista])))

motivo_selecionado = st.sidebar.multiselect(
    "⚠️ Motivo da Inelegibilidade:", 
    options=motivos_unicos, 
    default=[],
    help="Filtra alunos que possuam pelo menos um dos motivos selecionados."
)

if motivo_selecionado:
    df_filtrado = df_filtrado[df_filtrado['Lista_Motivos'].apply(lambda x: any(m in x for m in motivo_selecionado))]

estudantes = sorted(df_filtrado['Nome'].dropna().unique().tolist())
estudante_selecionado = st.sidebar.multiselect("🎓 Selecione o Estudante (Opcional):", options=estudantes, default=[])
if estudante_selecionado:
    df_filtrado = df_filtrado[df_filtrado['Nome'].isin(estudante_selecionado)]

# ==========================
# DETALHAMENTO DO ESTUDANTE
# ==========================
if estudante_selecionado:
    st.subheader("👤 Detalhamento da Elegibilidade do Estudante")
    
    colunas_exibicao = [
        'Nome', 'CPF Formatado', 'NIS Formatado', 'Etapa de Ensino (Traduzida)', 
        'Situação', 'Motivos_Formatados'
    ]
    
    df_detalhe = df_filtrado[colunas_exibicao].copy()
    
    df_detalhe.rename(columns={
        'CPF Formatado': 'CPF',
        'NIS Formatado': 'NIS',
        'Etapa de Ensino (Traduzida)': 'Etapa de Ensino',
        'Motivos_Formatados': 'Motivos / Pendências'
    }, inplace=True)
    
    st.table(df_detalhe.set_index('Nome'))
    
    st.markdown("**Instruções de Correção detalhadas:**")
    for index, row in df_filtrado.iterrows():
        st.info(f"**{row['Nome']}**: {row['Descrição']}")
    st.markdown("---")

# ==========================
# MÉTRICAS PRINCIPAIS (KPIs)
# ==========================
st.subheader("📈 Resumo da Elegibilidade")
col1, col2, col3, col4 = st.columns(4)

total_alunos = len(df_filtrado)
elegiveis = len(df_filtrado[df_filtrado['Situação'] == 'Elegível'])
nao_elegiveis = len(df_filtrado[df_filtrado['Situação'] == 'Não elegível'])

if total_alunos > 0:
    pct_elegivel = (elegiveis / total_alunos) * 100
else:
    pct_elegivel = 0

col1.metric("Total de Estudantes Analisados", total_alunos)
col2.metric("Elegíveis", elegiveis)
col3.metric("Não Elegíveis (Com pendências)", nao_elegiveis)
col4.metric("Taxa de Elegibilidade", f"{pct_elegivel:.1f}%")

st.markdown("---")

# ==========================
# GRÁFICOS DE ANÁLISE
# ==========================
if not df_filtrado.empty:
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.markdown("#### Proporção de Elegibilidade")
        sit_counts = df_filtrado['Situação'].value_counts().reset_index()
        sit_counts.columns = ['Situação', 'Quantidade']
        fig_sit = px.pie(sit_counts, values='Quantidade', names='Situação', hole=0.4, 
                         color='Situação',
                         color_discrete_map={'Elegível': '#2ca02c', 'Não elegível': '#d62728'})
        st.plotly_chart(fig_sit, use_container_width=True)

    with col_graf2:
        st.markdown("#### Inelegibilidade por Etapa de Ensino")
        df_nao_elegivel = df_filtrado[df_filtrado['Situação'] == 'Não elegível']
        if not df_nao_elegivel.empty:
            
            # 1. Agrupa contando as quantidades, mas mantém a coluna de ordenação
            etapa_counts = df_nao_elegivel.groupby(['Etapa de Ensino (Traduzida)', 'Ordem_Etapa']).size().reset_index(name='Quantidade')
            
            # 2. Ordena o dataframe com base na coluna numérica (25, 26, 30, 31...)
            etapa_counts = etapa_counts.sort_values(by='Ordem_Etapa')
            
            # 3. Quebra de linha no rótulo
            etapa_counts['Etapa de Ensino Visual'] = etapa_counts['Etapa de Ensino (Traduzida)'].apply(
                lambda x: "<br>".join(textwrap.wrap(str(x), width=18))
            )

            fig_etapa = px.bar(etapa_counts, x='Etapa de Ensino Visual', y='Quantidade', 
                               text_auto=True,
                               color_discrete_sequence=['#d62728'])
            
            # 4. Força o Plotly a não reorganizar as categorias (categoryorder = 'array')
            fig_etapa.update_layout(
                xaxis={'categoryorder':'array', 'categoryarray': etapa_counts['Etapa de Ensino Visual'].tolist()}
            )
            
            st.plotly_chart(fig_etapa, use_container_width=True)
        else:
            st.success("Nenhum aluno inelegível para os filtros selecionados!")

    st.markdown("#### Principais Motivos de Inelegibilidade")
    todos_motivos_grafico = [motivo for sublista in df_filtrado['Lista_Motivos'].tolist() for motivo in sublista]
    
    if todos_motivos_grafico:
        df_motivos_contagem = pd.Series(todos_motivos_grafico).value_counts().reset_index()
        df_motivos_contagem.columns = ['Motivo Completo', 'Quantidade']
        
        df_motivos_contagem['Motivo (Resumo)'] = df_motivos_contagem['Motivo Completo'].apply(
            lambda x: str(x)[:70] + '...' if len(str(x)) > 70 else str(x)
        )
        
        df_motivos_contagem['Motivo Completo'] = df_motivos_contagem['Motivo Completo'].apply(
            lambda x: "<br>".join(textwrap.wrap(str(x), width=80))
        )
        
        fig_motivos = px.bar(df_motivos_contagem, y='Motivo (Resumo)', x='Quantidade', 
                             orientation='h', color='Quantidade', 
                             color_continuous_scale='Reds',
                             hover_data={'Motivo Completo': True, 'Motivo (Resumo)': False})
        
        altura_dinamica = max(300, len(df_motivos_contagem) * 45)
        
        fig_motivos.update_layout(
            yaxis={'categoryorder':'total ascending'},
            height=altura_dinamica
        )
        st.plotly_chart(fig_motivos, use_container_width=True)
    else:
        st.info("Não há motivos de inelegibilidade para os dados atuais (todos estão elegíveis ou os dados estão vazios).")
else:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")