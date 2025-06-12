# Guia de Deploy no Render

Este guia fornece instruções detalhadas para deploy da API Orbit no Render.com, garantindo uma aplicação permanentemente disponível.

## Pré-requisitos

- Conta no Render.com (já integrada com GitHub)
- Repositório GitHub com o código da aplicação
- Estrutura do projeto conforme este pacote

## Deploy Manual via Painel do Render

### 1. Preparação do Repositório

1. Faça login no GitHub com suas credenciais
2. Crie um novo repositório (ex: `orbit-api-production`)
3. Clone o repositório localmente:
   ```bash
   git clone https://github.com/seu-usuario/orbit-api-production.git
   ```
4. Copie todos os arquivos deste pacote para o repositório
5. Faça commit e push:
   ```bash
   git add .
   git commit -m "Preparação para deploy no Render"
   git push origin master
   ```

### 2. Deploy no Render

1. Acesse [dashboard.render.com](https://dashboard.render.com)
2. Clique em "New" e selecione "Web Service"
3. Na seção "Connect a repository", selecione o repositório `orbit-api-production`
4. Configure o serviço:
   - **Nome**: orbit-api-production
   - **Região**: Oregon (ou a mais próxima)
   - **Branch**: master
   - **Ambiente**: Docker
   - **Dockerfile Path**: ./Dockerfile
   - **Health Check Path**: /api/health
   - **Plano**: Free

5. Configure as variáveis de ambiente:
   - `SECRET_KEY`: orbit-secret-key-production-2025
   - `DATABASE_URL`: sqlite:///data/orbit.db
   - `PORT`: 10000
   - `FLASK_ENV`: production
   - `CORS_ORIGINS`: *
   - `LOG_LEVEL`: INFO

6. Clique em "Create Web Service"

### 3. Monitoramento do Deploy

1. O Render iniciará automaticamente o processo de build e deploy
2. Acompanhe o progresso na aba "Events"
3. Aguarde até que o status mude para "Live"
4. A URL do serviço será exibida (formato: https://orbit-api-production.onrender.com)

## Configuração do PostgreSQL (Opcional, Recomendado)

Para usar PostgreSQL em vez de SQLite:

1. No painel do Render, clique em "New" e selecione "PostgreSQL"
2. Configure o banco de dados:
   - **Nome**: orbit-db
   - **Plano**: Free
   - **Região**: A mesma do Web Service

3. Após a criação, copie a "Internal Database URL"
4. Volte ao seu Web Service, vá para "Environment" e atualize:
   - `DATABASE_URL`: [Internal Database URL copiada]

5. Clique em "Save Changes" e aguarde o redeploy automático

## Verificação do Deploy

1. Acesse a URL do serviço + `/api/health`:
   ```
   https://orbit-api-production.onrender.com/api/health
   ```

2. Você deve receber uma resposta JSON com status "healthy"

3. Teste o login com as credenciais padrão:
   ```bash
   curl -X POST https://orbit-api-production.onrender.com/api/login \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"password"}'
   ```

## Integração com Frontend

Para conectar o frontend à API:

1. Atualize a variável `VITE_API_URL` no frontend para apontar para a URL do Render:
   ```
   VITE_API_URL=https://orbit-api-production.onrender.com
   ```

2. Reconstrua o frontend e faça deploy

## Manutenção e Atualizações

Para atualizar a aplicação:

1. Faça as alterações no código localmente
2. Commit e push para o GitHub:
   ```bash
   git add .
   git commit -m "Descrição das alterações"
   git push origin master
   ```

3. O Render detectará as alterações e fará o redeploy automaticamente

## Solução de Problemas

### API Offline ou Erro 503

O plano gratuito do Render desativa serviços após 15 minutos de inatividade. Na primeira requisição após inatividade, pode haver um atraso de até 30 segundos para reiniciar o serviço.

Solução: Implemente um mecanismo de retry no frontend ou use um serviço de ping para manter a API ativa.

### Erros de Banco de Dados

Se estiver usando SQLite e enfrentar problemas de persistência:

1. Verifique se o diretório `/app/data` está sendo criado corretamente
2. Considere migrar para PostgreSQL conforme instruções acima

### Logs e Depuração

1. No painel do Render, acesse seu serviço
2. Clique na aba "Logs" para visualizar logs em tempo real
3. Use o filtro para encontrar mensagens específicas

## Considerações de Produção

- O plano gratuito do Render tem limitações de recursos e tempo de atividade
- Para aplicações críticas, considere atualizar para um plano pago
- Configure alertas de monitoramento para ser notificado sobre problemas
- Implemente backups regulares do banco de dados
