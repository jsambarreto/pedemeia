import streamlit as st
import pandas as pd
import re
import unicodedata # <-- Biblioteca nova para remover acentos

# Configuração da página
st.set_page_config(page_title="Comparador SUAP x SGP", layout="wide")
st.title("⚖️ Comparador de Matrículas (SUAP x Pé-de-Meia)")
st.markdown("""
Esta ferramenta cruza os dados dos alunos matriculados no seu sistema acadêmico (SUAP) com a base do MEC (SGP). 
O objetivo é identificar rapidamente **quem está no SUAP, mas ficou de fora do Pé-de-Meia**.
""")

# ==========================
# FUNÇÕES DE LIMPEZA
# ==========================
def limpar_nome(nome):
    if pd.isna(nome): return ""
    # 1. Padroniza maiúsculas e remove espaços duplos
    nome_str = " ".join(str(nome).strip().upper().split())
    # 2. Remove acentos e cedilhas (Á -> A, Ç -> C)
    nome_sem_acento = unicodedata.normalize('NFKD', nome_str).encode('ASCII', 'ignore').decode('utf-8')
    return nome_sem_acento

def limpar_cpf(cpf):
    if pd.isna(cpf) or str(cpf).strip() in ['', 'nan', '0.0', 'None']:
        return ""
    val = str(cpf).strip()
    
    # Se o Excel importou como notação científica
    try:
        if 'e+' in val.lower() or ('.' in val and val.replace('.', '', 1).isdigit()):
            val = str(int(float(val)))
    except:
        pass
        
    # Remove tudo que não for número
    numeros = re.sub(r'\D', '', val)
    return numeros.zfill(11) if len(numeros) > 0 else ""

@st.cache_data
def carregar_arquivo(file):
    if file.name.endswith('.csv'):
        return pd.read_csv(file, dtype=str)
    else:
        df = pd.read_excel(file, dtype=str)
        if any("Unnamed" in str(col) for col in df.columns):
            df = pd.read_excel(file, header=1, dtype=str)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        return df

# ==========================
# UPLOAD DOS ARQUIVOS
# ==========================
col_upload1, col_upload2 = st.columns(2)

with col_upload1:
    st.info("🎓 **Passo 1:** Arquivo do SUAP (Alunos Matriculados)")
    file_suap = st.file_uploader("Upload da listagem do SUAP (.xls, .xlsx, .csv)", type=["xls", "xlsx", "csv"], key="suap")

with col_upload2:
    st.success("🏦 **Passo 2:** Arquivo de Elegibilidade (Pé-de-Meia / SGP)")
    file_sgp = st.file_uploader("Upload da planilha do MEC (.xlsx)", type=["xlsx"], key="sgp")

st.markdown("---")

# ==========================
# PROCESSAMENTO DA COMPARAÇÃO
# ==========================
if file_suap and file_sgp:
    try:
        with st.spinner("Processando, removendo acentos e cruzando os dados..."):
            df_suap = carregar_arquivo(file_suap)
            df_sgp = carregar_arquivo(file_sgp)
            
            st.sidebar.header("⚙️ Configurações das Colunas")
            st.sidebar.markdown("Confirme se o sistema detectou as colunas corretamente:")
            
            cols_suap = df_suap.columns.tolist()
            idx_nome_suap = cols_suap.index('Nome') if 'Nome' in cols_suap else (cols_suap.index('NOME') if 'NOME' in cols_suap else 0)
            idx_cpf_suap = cols_suap.index('CPF') if 'CPF' in cols_suap else (cols_suap.index('cpf') if 'cpf' in cols_suap else 0)
            
            col_nome_suap = st.sidebar.selectbox("Coluna de NOME (SUAP):", cols_suap, index=idx_nome_suap)
            col_cpf_suap = st.sidebar.selectbox("Coluna de CPF (SUAP):", cols_suap, index=idx_cpf_suap)
            
            col_nome_sgp = 'Nome'
            col_cpf_sgp = 'CPF'

            # Criação das chaves de cruzamento (Agora sem acentos!)
            df_suap['Nome_Limpo'] = df_suap[col_nome_suap].apply(limpar_nome)
            df_suap['CPF_Limpo'] = df_suap[col_cpf_suap].apply(limpar_cpf)
            
            df_sgp['Nome_Limpo'] = df_sgp[col_nome_sgp].apply(limpar_nome)
            df_sgp['CPF_Limpo'] = df_sgp[col_cpf_sgp].apply(limpar_cpf)
            
            df_suap_valido = df_suap[df_suap['Nome_Limpo'] != '']
            df_sgp_valido = df_sgp[df_sgp['Nome_Limpo'] != '']

            nomes_suap = set(df_suap_valido['Nome_Limpo'])
            nomes_sgp = set(df_sgp_valido['Nome_Limpo'])
            
            cpfs_suap = set(df_suap_valido['CPF_Limpo'])
            cpfs_sgp = set(df_sgp_valido['CPF_Limpo'])

            # ==========================
            # RESULTADOS NA TELA
            # ==========================
            tab1, tab2 = st.tabs(["🔍 Comparação por NOME", "🆔 Comparação por CPF"])
            
            # TAB 1: NOME
            with tab1:
                faltando_nome = nomes_suap - nomes_sgp
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Alunos no SUAP", len(nomes_suap))
                c2.metric("Alunos no SGP (MEC)", len(nomes_sgp))
                c3.metric("Faltando no Pé-de-Meia (por Nome)", len(faltando_nome), delta_color="inverse")
                
                if len(faltando_nome) > 0:
                    st.warning(f"**{len(faltando_nome)}** alunos estão no SUAP, mas seus nomes não constam na planilha do SGP.")
                    
                    df_resultado_nome = df_suap[df_suap['Nome_Limpo'].isin(faltando_nome)]
                    
                    colunas_exibir = [col_nome_suap, col_cpf_suap]
                    if 'Situação no Curso' in df_suap.columns: colunas_exibir.append('Situação no Curso')
                    if 'Curso' in df_suap.columns: colunas_exibir.append('Curso')
                    if 'Matrícula' in df_suap.columns: colunas_exibir.insert(0, 'Matrícula')
                    
                    st.dataframe(df_resultado_nome[colunas_exibir], use_container_width=True)
                else:
                    st.success("Excelente! Todos os nomes do SUAP foram encontrados na base do SGP.")
            
            # TAB 2: CPF
            with tab2:
                cpfs_suap_validos = {cpf for cpf in cpfs_suap if len(cpf) == 11}
                cpfs_sgp_validos = {cpf for cpf in cpfs_sgp if len(cpf) == 11}
                
                faltando_cpf = cpfs_suap_validos - cpfs_sgp_validos
                
                c1, c2, c3 = st.columns(3)
                c1.metric("CPFs Válidos no SUAP", len(cpfs_suap_validos))
                c2.metric("CPFs Válidos no SGP", len(cpfs_sgp_validos))
                c3.metric("CPFs Faltando no Pé-de-Meia", len(faltando_cpf), delta_color="inverse")
                
                if len(faltando_cpf) > 0:
                    st.warning(f"**{len(faltando_cpf)}** CPFs válidos estão no SUAP, mas não constam na planilha do SGP.")
                    
                    df_resultado_cpf = df_suap[df_suap['CPF_Limpo'].isin(faltando_cpf)]
                    
                    st.dataframe(df_resultado_cpf[colunas_exibir], use_container_width=True)
                else:
                    st.success("Excelente! Todos os CPFs válidos do SUAP constam na base do SGP.")
                    
    except Exception as e:
        st.error(f"Erro crítico ao cruzar os dados. Verifique o formato dos arquivos. Detalhe técnico: {e}")
else:
    st.info("Aguardando o upload de ambas as planilhas para iniciar a comparação...")