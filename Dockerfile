# Usar uma imagem base oficial e leve do Python
FROM python:3.10-slim

# Definir o diretório de trabalho dentro do container
WORKDIR /app

# Copiar o arquivo de dependências para o container
COPY requirements.txt .

# Instalar as bibliotecas (streamlit, pandas, plotly, openpyxl, xlrd)
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo o código do projeto (Inicio.py, pasta pages/, etc.)
COPY . .

# Expor a porta padrão do Streamlit
EXPOSE 8501

# Comando para iniciar o Streamlit
CMD ["streamlit", "run", "Inicio.py", "--server.port=8501", "--server.address=0.0.0.0"]