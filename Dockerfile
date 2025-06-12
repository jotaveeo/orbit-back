FROM python:3.11-slim

# Definir diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro para aproveitar cache do Docker
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY src/ ./src/

# Criar diretório para banco de dados com permissões adequadas
RUN mkdir -p /app/data && chmod 777 /app/data

# Expor porta
EXPOSE 5000

# Variáveis de ambiente padrão
ENV FLASK_ENV=production
ENV PORT=5000
ENV DATABASE_URL=sqlite:///data/orbit.db

# Comando para iniciar a aplicação
CMD ["python", "src/main.py"]
