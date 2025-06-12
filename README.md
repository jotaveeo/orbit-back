# Orbit API - Guia de Deploy

Este guia fornece instruções detalhadas para deploy da API Orbit em ambientes locais e de produção.

## Requisitos

- Python 3.11+
- Docker (opcional, para containerização)
- PostgreSQL (recomendado para produção)
- Git

## Estrutura do Projeto

```
orbit_production/
├── src/                # Código fonte da aplicação
├── tests/              # Testes automatizados
├── .env.example        # Exemplo de variáveis de ambiente
├── .env                # Variáveis de ambiente (não versionado)
├── Dockerfile          # Configuração Docker
├── render.yaml         # Configuração para deploy no Render
├── requirements.txt    # Dependências Python
└── README.md           # Este arquivo
```

## Deploy Local

### 1. Configuração do Ambiente

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/orbit-api.git
cd orbit-api

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Copiar arquivo de exemplo e configurar variáveis
cp .env.example .env
# Editar .env conforme necessário
```

### 2. Executar a Aplicação

```bash
# Iniciar a aplicação
python src/main.py
```

A API estará disponível em `http://localhost:5000`

### 3. Executar Testes

```bash
# Executar testes automatizados
python -m pytest tests/
```

## Deploy em Produção (Render)

### 1. Via GitHub (Recomendado)

1. Faça fork ou clone do repositório para sua conta GitHub
2. Acesse [dashboard.render.com](https://dashboard.render.com)
3. Clique em "New" e selecione "Web Service"
4. Conecte sua conta GitHub e selecione o repositório
5. Selecione a branch principal (main/master)
6. Configure o serviço:
   - Nome: orbit-api
   - Ambiente: Docker
   - Região: Escolha a mais próxima
   - Plano: Free (ou outro conforme necessidade)
7. Adicione as variáveis de ambiente:
   - SECRET_KEY
   - DATABASE_URL (PostgreSQL recomendado)
   - FLASK_ENV=production
   - CORS_ORIGINS
8. Clique em "Create Web Service"

### 2. Via Docker Local

```bash
# Construir a imagem
docker build -t orbit-api .

# Executar o container
docker run -p 5000:5000 --env-file .env orbit-api
```

### 3. Via Render CLI (Alternativa)

```bash
# Instalar Render CLI (se disponível)
npm install -g @render/cli

# Fazer login
render login

# Deploy
render deploy
```

## Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| SECRET_KEY | Chave secreta para JWT | orbit-secret-key-production-2025 |
| DATABASE_URL | URL de conexão com banco de dados | sqlite:///orbit.db |
| PORT | Porta da aplicação | 5000 |
| FLASK_ENV | Ambiente (development/production) | production |
| CORS_ORIGINS | Origens permitidas para CORS | * |
| LOG_LEVEL | Nível de logging | INFO |

## PostgreSQL no Render (Recomendado)

Para usar PostgreSQL no Render:

1. Crie um novo serviço PostgreSQL no Render
2. Copie a "Internal Database URL" 
3. Configure a variável DATABASE_URL com este valor
4. Adicione `psycopg2-binary` ao requirements.txt

## Monitoramento e Logs

- Acesse logs via dashboard do Render
- Configure alertas para monitoramento de saúde
- Use o endpoint `/api/health` para verificar status

## Segurança

- Mantenha SECRET_KEY seguro e único para cada ambiente
- Restrinja CORS_ORIGINS em produção
- Use HTTPS em produção (configurado automaticamente pelo Render)
- Implemente rate limiting para endpoints sensíveis

## Suporte

Para suporte, entre em contato com a equipe de desenvolvimento.
 