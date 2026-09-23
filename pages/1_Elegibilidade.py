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
    
    # Coluna para ordenar internamente as etapas (25, 26, 30, 31...)
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

# Inicializamos todas as variáveis como listas vazias para evitar NameError
unidade_selecionada = []
situacao_selecionada = []
etapa_selecionada = []
motivo_selecionado = []
estudante_selecionado = []

if 'Nome da Unidade de Ensino' in df_filtrado.columns:
    unidades = sorted(df_filtrado['Nome da Unidade de Ensino'].dropna().unique().tolist())
    unidade_selecionada = st.sidebar.multiselect("🏫 Selecione o(s) Campus:", options=unidades, default=[])
    if unidade_selecionada:
        df_filtrado = df_filtrado[df_filtrado['Nome da Unidade de Ensino'].isin(unidade_selecionada)]

if 'Situação' in df_filtrado.columns:
    situacoes = sorted(df_filtrado['Situação'].dropna().unique().tolist())
    situacao_selecionada = st.sidebar.multiselect("🎯 Situação:", options=situacoes, default=[])
    if situacao_selecionada:
        df_filtrado = df_filtrado[df_filtrado['Situação'].isin(situacao_selecionada)]

if 'Etapa de Ensino (Traduzida)' in df_filtrado.columns:
    etapas = df_filtrado[['Ordem_Etapa', 'Etapa de Ensino (Traduzida)']].drop_duplicates().sort_values(by='Ordem_Etapa')['Etapa de Ensino (Traduzida)'].tolist()
    etapa_selecionada = st.sidebar.multiselect("📚 Etapa de Ensino:", options=etapas, default=[])
    if etapa_selecionada:
        df_filtrado = df_filtrado[df_filtrado['Etapa de Ensino (Traduzida)'].isin(etapa_selecionada)]

if 'Situação' in df_filtrado.columns:
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

if 'Nome' in df_filtrado.columns:
    estudantes = sorted(df_filtrado['Nome'].dropna().unique().tolist())
    estudante_selecionado = st.sidebar.multiselect("🎓 Selecione o Estudante (Opcional):", options=estudantes, default=[])
    if estudante_selecionado:
        df_filtrado = df_filtrado[df_filtrado['Nome'].isin(estudante_selecionado)]


# ==========================
# LÓGICA DE EXIBIÇÃO CONDICIONAL
# ==========================
if estudante_selecionado:
    # ---------------------------------------------------------
    # VISÃO DO ESTUDANTE
    # ---------------------------------------------------------
    st.subheader("👤 Detalhamento da Elegibilidade do Estudante")
    
    colunas_exibicao = [
        'Nome', 'CPF Formatado', 'NIS Formatado', 'Etapa de Ensino (Traduzida)', 
        'Situação', 'Motivos_Formatados'
    ]
    colunas_exibicao = [col for col in colunas_exibicao if col in df_filtrado.columns]
    
    df_detalhe = df_filtrado[colunas_exibicao].copy()
    df_detalhe.rename(columns={
        'CPF Formatado': 'CPF',
        'NIS Formatado': 'NIS',
        'Etapa de Ensino (Traduzida)': 'Etapa de Ensino',
        'Motivos_Formatados': 'Motivos / Pendências'
    }, inplace=True, errors='ignore')
    
    st.table(df_detalhe.set_index('Nome'))
    
    st.markdown("**Instruções de Correção detalhadas:**")
    for index, row in df_filtrado.iterrows():
        st.info(f"**{row['Nome']}**: {row.get('Descrição', 'Sem descrição disponível')}")

else:
    # ---------------------------------------------------------
    # VISÃO GERAL (Dashboard completo)
    # ---------------------------------------------------------
    st.subheader("📈 Resumo da Elegibilidade")
    col1, col2, col3, col4 = st.columns(4)
    
    total_alunos = len(df_filtrado)
    elegiveis = len(df_filtrado[df_filtrado['Situação'] == 'Elegível']) if 'Situação' in df_filtrado.columns else 0
    nao_elegiveis = len(df_filtrado[df_filtrado['Situação'] == 'Não elegível']) if 'Situação' in df_filtrado.columns else 0
    
    pct_elegivel = (elegiveis / total_alunos) * 100 if total_alunos > 0 else 0
    
    col1.metric("Total de Estudantes Analisados", total_alunos)
    col2.metric("Elegíveis", elegiveis)
    col3.metric("Não Elegíveis (Com pendências)", nao_elegiveis)
    col4.metric("Taxa de Elegibilidade", f"{pct_elegivel:.1f}%")
    
    st.markdown("---")
    
    if not df_filtrado.empty:
        col_graf1, col_graf2 = st.columns(2)
    
        with col_graf1:
            if not situacao_selecionada and 'Situação' in df_filtrado.columns:
                st.markdown("#### Proporção de Elegibilidade")
                sit_counts = df_filtrado['Situação'].value_counts().reset_index()
                sit_counts.columns = ['Situação', 'Quantidade']
                fig_sit = px.pie(sit_counts, values='Quantidade', names='Situação', hole=0.4, 
                                 color='Situação',
                                 color_discrete_map={'Elegível': '#2ca02c', 'Não elegível': '#d62728'})
                st.plotly_chart(fig_sit, use_container_width=True)
            else:
                st.info("💡 Gráfico de proporções ocultado porque há um filtro de Situação ativo.")
    
        with col_graf2:
            # Só faz sentido mostrar gráfico de inelegibilidade se houver alunos não elegíveis visíveis
            df_nao_elegivel = df_filtrado[df_filtrado['Situação'] == 'Não elegível'] if 'Situação' in df_filtrado.columns else pd.DataFrame()
            
            if not df_nao_elegivel.empty and 'Etapa de Ensino (Traduzida)' in df_nao_elegivel.columns:
                st.markdown("#### Inelegibilidade por Etapa de Ensino")
                etapa_counts = df_nao_elegivel.groupby(['Etapa de Ensino (Traduzida)', 'Ordem_Etapa']).size().reset_index(name='Quantidade')
                etapa_counts = etapa_counts.sort_values(by='Ordem_Etapa')
                
                etapa_counts['Etapa de Ensino Visual'] = etapa_counts['Etapa de Ensino (Traduzida)'].apply(
                    lambda x: "<br>".join(textwrap.wrap(str(x), width=18))
                )
    
                fig_etapa = px.bar(etapa_counts, x='Etapa de Ensino', y='Quantidade', 
                                   text_auto=True, color_discrete_sequence=['#d62728'])
                fig_etapa.update_layout(xaxis={'categoryorder':'array', 'categoryarray': etapa_counts['Etapa de Ensino'].tolist()})
                st.plotly_chart(fig_etapa, use_container_width=True)
            else:
                st.success("Nenhum aluno inelegível encontrado para exibir neste gráfico.")
    
        # Gráfico de Motivos
        st.markdown("#### Principais Motivos de Inelegibilidade")
        todos_motivos_grafico = [motivo for sublista in df_filtrado['Lista_Motivos'].tolist() for motivo in sublista] if 'Lista_Motivos' in df_filtrado.columns else []
        
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
                                 orientation='h', color='Quantidade', color_continuous_scale='Reds',
                                 hover_data={'Motivo Completo': True, 'Motivo (Resumo)': False})
            
            altura_dinamica = max(300, len(df_motivos_contagem) * 45)
            fig_motivos.update_layout(yaxis={'categoryorder':'total ascending'}, height=altura_dinamica)
            st.plotly_chart(fig_motivos, use_container_width=True)
        else:
            st.info("Não há motivos de inelegibilidade para os dados atuais (todos estão elegíveis ou a base está limpa).")
            
    # ---------------------------------------------------------
    # TABELA DE DETALHAMENTO GERAL
    # ---------------------------------------------------------
    st.markdown("---")
    st.subheader("📋 Lista de Estudantes Filtrados")
    
    if not df_filtrado.empty:
        st.write(f"A apresentar **{len(df_filtrado)}** registo(s) com base nos filtros selecionados.")
        
        colunas_desejadas = [
            'Nome', 'CPF Formatado', 'Etapa de Ensino (Traduzida)', 
            'Situação', 'Motivos_Formatados'
        ]
        
        colunas_exibicao = [col for col in colunas_desejadas if col in df_filtrado.columns]
        if not colunas_exibicao:
            colunas_exibicao = df_filtrado.columns.tolist()
            
        df_tabela = df_filtrado[colunas_exibicao].copy()
        
        df_tabela.rename(columns={
            'CPF Formatado': 'CPF',
            'Etapa de Ensino (Traduzida)': 'Etapa de Ensino',
            'Motivos_Formatados': 'Motivos / Pendências'
        }, inplace=True, errors='ignore')
        
        st.dataframe(df_tabela, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum estudante encontrado com os filtros atuais.")