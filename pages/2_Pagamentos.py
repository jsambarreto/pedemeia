import streamlit as st
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="Dashboard de Pagamentos", layout="wide")
st.title("💸 Dashboard de Pagamentos - Pé-de-Meia")

@st.cache_data
def load_data(file):
    df = pd.read_excel(file, header=1)
    
    # Tratamento básico de nulos
    if 'Nome da Unidade de Ensino' in df.columns:
        df['Nome da Unidade de Ensino'] = df['Nome da Unidade de Ensino'].fillna('Não Informado')
    if 'Situação' in df.columns:
        df['Situação'] = df['Situação'].fillna('Desconhecida')
        
    # Extrair Ano e Mês se o formato for YYYYMM (ex: 202401)
    if 'Mês de referência' in df.columns:
        df['Mês de referência'] = df['Mês de referência'].fillna(0).astype(int).astype(str)
        df['Ano'] = df['Mês de referência'].apply(lambda x: x[:4] if len(x) == 6 else 'N/A')
        
        meses_map = {
            '01': '01 - Janeiro', '02': '02 - Fevereiro', '03': '03 - Março',
            '04': '04 - Abril', '05': '05 - Maio', '06': '06 - Junho',
            '07': '07 - Julho', '08': '08 - Agosto', '09': '09 - Setembro',
            '10': '10 - Outubro', '11': '11 - Novembro', '12': '12 - Dezembro'
        }
        df['Mês'] = df['Mês de referência'].apply(lambda x: meses_map.get(x[4:6], 'N/A') if len(x) == 6 else 'N/A')
    
    # Tratar a coluna Valor para somatório financeiro
    col_valor = 'Valor da parcela' if 'Valor da parcela' in df.columns else ('Valor' if 'Valor' in df.columns else None)
    if col_valor:
        # Se os dados vierem com 'R$' ou vírgulas, forçamos para número
        df['Valor Numérico'] = pd.to_numeric(df[col_valor].astype(str).str.replace('R$', '').str.replace(',', '.').str.strip(), errors='coerce').fillna(0)
    
    return df

# ==========================
# UPLOAD DE ARQUIVO
# ==========================
st.sidebar.header("📂 Base de Dados")
arquivo_carregado = st.sidebar.file_uploader("Faça o upload da planilha de Pagamentos do SGP (.xlsx)", type=["xlsx"])

if arquivo_carregado is None:
    st.info("👋 Bem-vindo à página de Pagamentos! Arraste a sua planilha de pagamentos para o menu lateral para iniciar.")
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

# Prevenção de NameError: Inicializamos todas as variáveis como listas vazias
unidade_selecionada = []
ano_selecionado = []
mes_selecionado = []
tipo_selecionado = []
situacao_selecionada = []
estudante_selecionado = []

# 1. Filtro de Campus
if 'Nome da Unidade de Ensino' in df_filtrado.columns:
    unidades = sorted(df_filtrado['Nome da Unidade de Ensino'].unique().tolist())
    unidade_selecionada = st.sidebar.multiselect("🏫 Selecione o(s) Campus:", options=unidades, default=[])
    if unidade_selecionada:
        df_filtrado = df_filtrado[df_filtrado['Nome da Unidade de Ensino'].isin(unidade_selecionada)]

# 2. Filtro de Ano e Mês
if 'Ano' in df_filtrado.columns and 'Mês' in df_filtrado.columns:
    anos = sorted(df_filtrado['Ano'].unique().tolist())
    ano_selecionado = st.sidebar.multiselect("📅 Ano:", options=anos, default=[])
    if ano_selecionado:
        df_filtrado = df_filtrado[df_filtrado['Ano'].isin(ano_selecionado)]
        
    meses = sorted(df_filtrado['Mês'].unique().tolist())
    mes_selecionado = st.sidebar.multiselect("🗓️ Mês:", options=meses, default=[])
    if mes_selecionado:
        df_filtrado = df_filtrado[df_filtrado['Mês'].isin(mes_selecionado)]

# 3. Filtro de Tipo de Incentivo
if 'Tipo de incentivo' in df_filtrado.columns:
    tipos = sorted(df_filtrado['Tipo de incentivo'].dropna().unique().tolist())
    tipo_selecionado = st.sidebar.multiselect("💰 Tipo de Incentivo:", options=tipos, default=[])
    if tipo_selecionado:
        df_filtrado = df_filtrado[df_filtrado['Tipo de incentivo'].isin(tipo_selecionado)]

# 4. Filtro de Situação
if 'Situação' in df_filtrado.columns:
    situacoes = sorted(df_filtrado['Situação'].dropna().unique().tolist())
    situacao_selecionada = st.sidebar.multiselect("🎯 Situação da Parcela:", options=situacoes, default=[])
    if situacao_selecionada:
        df_filtrado = df_filtrado[df_filtrado['Situação'].isin(situacao_selecionada)]

# 5. Filtro de Estudante
if 'Nome' in df_filtrado.columns:
    estudantes = sorted(df_filtrado['Nome'].dropna().unique().tolist())
    estudante_selecionado = st.sidebar.multiselect("🎓 Selecione o Estudante (Opcional):", options=estudantes, default=[])
    if estudante_selecionado:
        df_filtrado = df_filtrado[df_filtrado['Nome'].isin(estudante_selecionado)]

# ==========================
# LÓGICA DE EXIBIÇÃO CONDICIONAL
# ==========================

# STATUS CONSIDERADOS COMO PAGOS (Ajuste caso o SGP mude a nomenclatura)
situacoes_pagas = ["Pago", "Enviado para pagamento", "Crédito efetivado", "Efetivado", "Crédito Efetivado"]

if estudante_selecionado:
    # ---------------------------------------------------------
    # VISÃO DO ESTUDANTE (Oculta gráficos, foca no aluno)
    # ---------------------------------------------------------
    st.subheader("👤 Detalhamento do Estudante")
    
    colunas_exibicao_aluno = [
        'Nome', 'CPF', 'Mês', 'Tipo de incentivo', 
        'Situação', 'Descrição da parcela'
    ]
    # Garante que só puxamos colunas que existem na planilha importada
    colunas_exibicao_aluno = [col for col in colunas_exibicao_aluno if col in df_filtrado.columns]
    
    st.dataframe(df_filtrado[colunas_exibicao_aluno].set_index('Nome'), use_container_width=True)

else:
    # ---------------------------------------------------------
    # VISÃO GERAL (Dashboard completo)
    # ---------------------------------------------------------
    
    # --- KPIs ---
    st.subheader("📈 Resumo de Pagamentos")
    col1, col2, col3, col4 = st.columns(4)
    
    total_registos = len(df_filtrado)
    
    pagos = 0
    if 'Situação' in df_filtrado.columns:
        pagos = len(df_filtrado[df_filtrado['Situação'].isin(situacoes_pagas)])
    
    valor_total = 0
    if 'Valor Numérico' in df_filtrado.columns:
        valor_total = df_filtrado.loc[df_filtrado['Situação'].isin(situacoes_pagas), 'Valor Numérico'].sum()
    
    col1.metric("Total de Parcelas Analisadas", total_registos)
    col2.metric("Parcelas Pagas/Enviadas", pagos)
    
    pct_pago = (pagos / total_registos * 100) if total_registos > 0 else 0
    col3.metric("Taxa de Sucesso", f"{pct_pago:.1f}%")
        
    col4.metric("Volume Financeiro Pago", f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    
    st.markdown("---")
    
    # --- GRÁFICOS ---
    if not df_filtrado.empty:
        col_graf1, col_graf2 = st.columns(2)
        
        with col_graf1:
            if not situacao_selecionada and 'Situação' in df_filtrado.columns:
                st.markdown("#### Proporção das Situações")
                sit_counts = df_filtrado['Situação'].value_counts().reset_index()
                sit_counts.columns = ['Situação', 'Quantidade']
                fig_sit = px.pie(sit_counts, values='Quantidade', names='Situação', hole=0.4)
                st.plotly_chart(fig_sit, use_container_width=True)
            else:
                st.info("💡 Gráfico de proporções ocultado porque há um filtro de Situação ativo.")
                
        with col_graf2:
            # Lógica para mostrar ou esconder o gráfico financeiro
            mostrar_grafico_financeiro = False
            if not situacao_selecionada:
                mostrar_grafico_financeiro = True
            elif any(sit in situacoes_pagas for sit in situacao_selecionada):
                mostrar_grafico_financeiro = True
                
            if mostrar_grafico_financeiro and 'Valor Numérico' in df_filtrado.columns:
                st.markdown("#### Volume Pago por Tipo de Incentivo")
                
                df_pago = df_filtrado[df_filtrado['Situação'].isin(situacoes_pagas)]
                if not df_pago.empty and 'Tipo de incentivo' in df_pago.columns:
                    df_financeiro = df_pago.groupby('Tipo de incentivo')['Valor Numérico'].sum().reset_index()
                    fig_fin = px.bar(df_financeiro, x='Tipo de incentivo', y='Valor Numérico', text_auto='.2s')
                    st.plotly_chart(fig_fin, use_container_width=True)
                else:
                    st.warning("Nenhum valor pago identificado para os filtros atuais.")
            else:
                st.info("💡 Gráfico financeiro ocultado pois a situação filtrada não reflete parcelas pagas.")
    
    # --- TABELA DE DETALHAMENTO GERAL ---
    st.markdown("---")
    st.subheader("📋 Lista de Estudantes Filtrados")
    
    if not df_filtrado.empty:
        st.write(f"A apresentar **{len(df_filtrado)}** registo(s) com base nos filtros selecionados.")
        
        colunas_desejadas = [
            'Nome', 'CPF', 'Nome da Unidade de Ensino', 
            'Mês', 'Tipo de incentivo', 'Situação', 'Descrição da parcela'
        ]
        
        colunas_exibicao = [col for col in colunas_desejadas if col in df_filtrado.columns]
        if not colunas_exibicao:
            colunas_exibicao = df_filtrado.columns.tolist()
            
        df_tabela = df_filtrado[colunas_exibicao].copy()
        
        # Tabela interativa com botão nativo para download em CSV
        st.dataframe(df_tabela, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum estudante encontrado com os filtros atuais.")