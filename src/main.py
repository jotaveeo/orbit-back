from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import logging
from datetime import datetime, timedelta
import jwt  # <-- Adicione aqui
import bcrypt

from src import db
from src.models.user import User
from src.models.card import Card
from src.routes.user import user_bp

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configurações de ambiente
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'orbit-secret-key-2025')

# Garantir que DATABASE_URL nunca seja vazio e sempre use caminho absoluto para SQLite
database_url = os.environ.get('DATABASE_URL')
if not database_url:
    logger.warning("DATABASE_URL não definida, usando SQLite local como fallback")
    # Usar caminho absoluto para o banco de dados SQLite
    db_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data'))
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, 'orbit.db')
    database_url = f'sqlite:///{db_path}'
    logger.info(f"Criado diretório para banco de dados: {db_dir}")
    logger.info(f"Usando banco de dados SQLite em: {db_path}")
elif database_url.startswith('sqlite:///'):
    # Extrair o caminho do arquivo do SQLite
    db_path = database_url.replace('sqlite:///', '')
    
    # Converter para caminho absoluto se for relativo
    if not os.path.isabs(db_path):
        abs_db_path = os.path.abspath(os.path.join(os.getcwd(), db_path))
        logger.info(f"Convertendo caminho SQLite relativo para absoluto: {db_path} -> {abs_db_path}")
        db_path = abs_db_path
        database_url = f'sqlite:///{db_path}'
    
    # Criar diretório para o banco de dados
    db_dir = os.path.dirname(db_path)
    os.makedirs(db_dir, exist_ok=True)
    logger.info(f"Garantindo que o diretório do banco existe: {db_dir}")
    
    # Verificar permissões
    try:
        # Tentar criar um arquivo temporário para verificar permissões
        test_file = os.path.join(db_dir, '.test_write_permission')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
        logger.info(f"Diretório {db_dir} tem permissões de escrita")
    except Exception as e:
        logger.error(f"Erro ao verificar permissões no diretório {db_dir}: {str(e)}")
        # Tentar usar um diretório alternativo com permissões garantidas
        alt_db_dir = os.path.abspath(os.path.join(os.getcwd(), 'instance'))
        os.makedirs(alt_db_dir, exist_ok=True)
        alt_db_path = os.path.join(alt_db_dir, 'orbit.db')
        database_url = f'sqlite:///{alt_db_path}'
        logger.warning(f"Usando diretório alternativo para banco de dados: {alt_db_dir}")

# Corrigir prefixo postgres:// para postgresql:// (necessário para SQLAlchemy 1.4+)
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

logger.info(f"Configuração final do banco de dados: {database_url}")

# Inicializar extensões
db.init_app(app)
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

app.register_blueprint(user_bp, url_prefix='/api')

# Rotas
@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '2.0.0',
        'database': app.config['SQLALCHEMY_DATABASE_URI'],
        'environment': os.environ.get('FLASK_ENV', 'production'),
        'working_directory': os.getcwd(),
        'database_directory': os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')) if app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:///') else 'N/A'
    })

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'success': False, 'message': 'Username e password são obrigatórios'}), 400

        username = data['username']
        password = data['password']

        logger.info(f"Tentativa de login para usuário: {username}")

        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Gerar token JWT
            token = jwt.encode({
                'user_id': user.id,
                'username': user.username,
                'role': user.role,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm='HS256')

            logger.info(f"Login bem-sucedido para usuário: {username}")
            
            return jsonify({
                'success': True,
                'token': token,
                'user': user.to_dict()
            })
        else:
            logger.warning(f"Login falhou para usuário: {username}")
            return jsonify({'success': False, 'message': 'Credenciais inválidas'}), 401

    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500

@app.route('/api/cards', methods=['GET'])
def get_cards():
    try:
        cards = Card.query.all()
        return jsonify({
            'success': True,
            'cards': [card.to_dict() for card in cards]
        })
    except Exception as e:
        logger.error(f"Erro ao buscar cards: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao buscar cards'}), 500

@app.route('/api/cards', methods=['POST'])
def create_card():
    try:
        data = request.get_json()
        if not data or 'title' not in data:
            return jsonify({'success': False, 'message': 'Título é obrigatório'}), 400

        card = Card(
            title=data['title'],
            description=data.get('description', ''),
            status=data.get('status', 'pending'),
            priority=data.get('priority', 'medium')
        )
        
        db.session.add(card)
        db.session.commit()

        return jsonify({
            'success': True,
            'card': card.to_dict()
        }), 201

    except Exception as e:
        logger.error(f"Erro ao criar card: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao criar card'}), 500

@app.route('/api/sla', methods=['GET'])
def get_sla_metrics():
    try:
        # Métricas SLA simuladas
        metrics = {
            'sla_targets': {
                'requisicao_compra': {'target': 2, 'unit': 'dias'},
                'aprovacao_requisicao': {'target': 4, 'unit': 'dias'},
                'lancamento_nf': {'target': 2, 'unit': 'dias'}
            },
            'current_performance': {
                'requisicao_compra': {'average': 1.8, 'compliance': 95},
                'aprovacao_requisicao': {'average': 3.2, 'compliance': 88},
                'lancamento_nf': {'average': 1.5, 'compliance': 98}
            },
            'deadlines': {
                'nf_mercadoria': 'Último dia útil do mês',
                'nf_servico': 'Dia 24 de cada mês'
            }
        }
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
    except Exception as e:
        logger.error(f"Erro ao buscar métricas SLA: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro ao buscar métricas'}), 500

@app.route('/api/kanban-data', methods=['GET'])
def kanban_data():
    return jsonify({'success': True, 'data': []})

@app.route('/api/dashboard-stats', methods=['GET'])
def dashboard_stats():
    try:
        total_requisicoes = Card.query.count()
        valor_total = db.session.query(db.func.sum(Card.Valor_Estimado)).scalar() or 0
        status_distribution = {}
        for status in ["Solicitado", "Em Análise", "Aprovado", "Recebido", "Rejeitado"]:
            status_distribution[status] = Card.query.filter_by(Status=status).count()
        data = {
            "total_requisicoes": total_requisicoes,
            "valor_total": valor_total,
            "status_distribution": status_distribution
        }
        return jsonify({"success": True, "data": data})
    except Exception as e:
        logger.error(f"Erro ao buscar dashboard stats: {str(e)}")
        return jsonify({"success": False, "message": "Erro ao buscar estatísticas"}), 500

@app.route('/api/dashboard-stats', methods=['OPTIONS'])
def dashboard_stats_options():
    return '', 200

def create_default_users():
    """Criar usuários padrão se não existirem"""
    try:
        if User.query.count() == 0:
            users = [
                {'username': 'admin', 'password': 'password', 'role': 'Administrador'},
                {'username': 'manager', 'password': 'password', 'role': 'Gerente de Setor'},
                {'username': 'user', 'password': 'password', 'role': 'Analista Backoffice'}
            ]
            
            for user_data in users:
                password_hash = bcrypt.hashpw(user_data['password'].encode('utf-8'), bcrypt.gensalt())
                user = User(
                    username=user_data['username'],
                    password_hash=password_hash,
                    role=user_data['role']
                )
                db.session.add(user)
            
            db.session.commit()
            logger.info("Usuários padrão criados com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar usuários padrão: {str(e)}")

def create_sample_cards():
    """Criar cards de exemplo se não existirem"""
    try:
        if Card.query.count() == 0:
            sample_cards = [
                {
                    "ID_RC": "RC-2025-001",
                    "Criado_Por": "admin",
                    "Valor_Estimado": 1500.00,
                    "Status": "Solicitado",
                    "Tipo_Requisicao": "Padrão",
                    "Unidade": "Maracanaú",
                    "Fornecedor_Sugerido": "Fornecedor X",
                    "Data_Criacao": datetime.utcnow()
                },
                {
                    "ID_RC": "RC-2025-002",
                    "Criado_Por": "admin",
                    "Valor_Estimado": 300.00,
                    "Status": "Aprovado",
                    "Tipo_Requisicao": "Padrão",
                    "Unidade": "Fortaleza",
                    "Fornecedor_Sugerido": "Fornecedor Y",
                    "Data_Criacao": datetime.utcnow()
                },
                {
                    "ID_RC": "RC-2025-003",
                    "Criado_Por": "manager",
                    "Valor_Estimado": 1200.00,
                    "Status": "Em Análise",
                    "Tipo_Requisicao": "Contrato",
                    "Unidade": "Maracanaú",
                    "Fornecedor_Sugerido": "Fornecedor Z",
                    "Data_Criacao": datetime.utcnow()
                },
                {
                    "ID_RC": "RC-2025-004",
                    "Criado_Por": "user",
                    "Valor_Estimado": 950.00,
                    "Status": "Recebido",
                    "Tipo_Requisicao": "Contrato",
                    "Unidade": "Fortaleza",
                    "Fornecedor_Sugerido": "Fornecedor W",
                    "Data_Criacao": datetime.utcnow()
                },
                {
                    "ID_RC": "RC-2025-005",
                    "Criado_Por": "manager",
                    "Valor_Estimado": 500.00,
                    "Status": "Rejeitado",
                    "Tipo_Requisicao": "Interna",
                    "Unidade": "Maracanaú",
                    "Fornecedor_Sugerido": "Fornecedor Q",
                    "Data_Criacao": datetime.utcnow()
                },
                {
                    "ID_RC": "RC-2025-006",
                    "Criado_Por": "user",
                    "Valor_Estimado": 2000.00,
                    "Status": "Solicitado",
                    "Tipo_Requisicao": "Delegada",
                    "Unidade": "Fortaleza",
                    "Fornecedor_Sugerido": "Fornecedor A",
                    "Data_Criacao": datetime.utcnow()
                },
                {
                    "ID_RC": "RC-2025-007",
                    "Criado_Por": "manager",
                    "Valor_Estimado": 750.00,
                    "Status": "Aprovado",
                    "Tipo_Requisicao": "Contrato",
                    "Unidade": "Maracanaú",
                    "Fornecedor_Sugerido": "Fornecedor B",
                    "Data_Criacao": datetime.utcnow()
                },
                {
                    "ID_RC": "RC-2025-008",
                    "Criado_Por": "admin",
                    "Valor_Estimado": 1800.00,
                    "Status": "Em Análise",
                    "Tipo_Requisicao": "Padrão",
                    "Unidade": "Fortaleza",
                    "Fornecedor_Sugerido": "Fornecedor C",
                    "Data_Criacao": datetime.utcnow()
                },
                {
                    "ID_RC": "RC-2025-009",
                    "Criado_Por": "user",
                    "Valor_Estimado": 400.00,
                    "Status": "Recebido",
                    "Tipo_Requisicao": "Interna",
                    "Unidade": "Maracanaú",
                    "Fornecedor_Sugerido": "Fornecedor D",
                    "Data_Criacao": datetime.utcnow()
                },
                {
                    "ID_RC": "RC-2025-010",
                    "Criado_Por": "manager",
                    "Valor_Estimado": 600.00,
                    "Status": "Rejeitado",
                    "Tipo_Requisicao": "Delegada",
                    "Unidade": "Fortaleza",
                    "Fornecedor_Sugerido": "Fornecedor E",
                    "Data_Criacao": datetime.utcnow()
                },
                {
                    "ID_RC": "RC-2025-011",
                    "Criado_Por": "admin",
                    "Valor_Estimado": 1100.00,
                    "Status": "Solicitado",
                    "Tipo_Requisicao": "Contrato",
                    "Unidade": "Maracanaú",
                    "Fornecedor_Sugerido": "Fornecedor F",
                    "Data_Criacao": datetime.utcnow()
                },
                {
                    "ID_RC": "RC-2025-012",
                    "Criado_Por": "manager",
                    "Valor_Estimado": 2500.00,
                    "Status": "Aprovado",
                    "Tipo_Requisicao": "Delegada",
                    "Unidade": "Fortaleza",
                    "Fornecedor_Sugerido": "Fornecedor G",
                    "Data_Criacao": datetime.utcnow()
                },
                {
                    "ID_RC": "RC-2025-013",
                    "Criado_Por": "user",
                    "Valor_Estimado": 700.00,
                    "Status": "Em Análise",
                    "Tipo_Requisicao": "Interna",
                    "Unidade": "Maracanaú",
                    "Fornecedor_Sugerido": "Fornecedor H",
                    "Data_Criacao": datetime.utcnow()
                },
                {
                    "ID_RC": "RC-2025-014",
                    "Criado_Por": "admin",
                    "Valor_Estimado": 180.00,
                    "Status": "Recebido",
                    "Tipo_Requisicao": "Padrão",
                    "Unidade": "Fortaleza",
                    "Fornecedor_Sugerido": "Fornecedor I",
                    "Data_Criacao": datetime.utcnow()
                },
                {
                    "ID_RC": "RC-2025-015",
                    "Criado_Por": "manager",
                    "Valor_Estimado": 3200.00,
                    "Status": "Rejeitado",
                    "Tipo_Requisicao": "Contrato",
                    "Unidade": "Maracanaú",
                    "Fornecedor_Sugerido": "Fornecedor J",
                    "Data_Criacao": datetime.utcnow()
                },
                {
                    "ID_RC": "RC-2025-016",
                    "Criado_Por": "user",
                    "Valor_Estimado": 450.00,
                    "Status": "Solicitado",
                    "Tipo_Requisicao": "Interna",
                    "Unidade": "Fortaleza",
                    "Fornecedor_Sugerido": "Fornecedor K",
                    "Data_Criacao": datetime.utcnow()
                },
                {
                    "ID_RC": "RC-2025-017",
                    "Criado_Por": "admin",
                    "Valor_Estimado": 980.00,
                    "Status": "Aprovado",
                    "Tipo_Requisicao": "Delegada",
                    "Unidade": "Maracanaú",
                    "Fornecedor_Sugerido": "Fornecedor L",
                    "Data_Criacao": datetime.utcnow()
                },
                {
                    "ID_RC": "RC-2025-018",
                    "Criado_Por": "manager",
                    "Valor_Estimado": 2100.00,
                    "Status": "Em Análise",
                    "Tipo_Requisicao": "Padrão",
                    "Unidade": "Fortaleza",
                    "Fornecedor_Sugerido": "Fornecedor M",
                    "Data_Criacao": datetime.utcnow()
                },
                {
                    "ID_RC": "RC-2025-019",
                    "Criado_Por": "user",
                    "Valor_Estimado": 350.00,
                    "Status": "Recebido",
                    "Tipo_Requisicao": "Contrato",
                    "Unidade": "Maracanaú",
                    "Fornecedor_Sugerido": "Fornecedor N",
                    "Data_Criacao": datetime.utcnow()
                },
                {
                    "ID_RC": "RC-2025-020",
                    "Criado_Por": "admin",
                    "Valor_Estimado": 1600.00,
                    "Status": "Rejeitado",
                    "Tipo_Requisicao": "Delegada",
                    "Unidade": "Fortaleza",
                    "Fornecedor_Sugerido": "Fornecedor O",
                    "Data_Criacao": datetime.utcnow()
                }
            ]
            
            for card_data in sample_cards:
                card = Card(**card_data)
                db.session.add(card)
            
            db.session.commit()
            logger.info("Cards de exemplo criados com sucesso")
    except Exception as e:
        logger.error(f"Erro ao criar cards de exemplo: {str(e)}")

if __name__ == '__main__':
    # Mostrar informações do ambiente
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"Environment variables: DATABASE_URL={'set' if os.environ.get('DATABASE_URL') else 'not set'}")
    
    # Criar banco de dados e tabelas
    with app.app_context():
        try:
            db.create_all()
            logger.info("Banco de dados e tabelas criados com sucesso")
            create_default_users()
            create_sample_cards()
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {str(e)}")
            sys.exit(1)
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
