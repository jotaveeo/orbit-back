import unittest
import json
import sys
import os

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app, db, User, Card

class OrbitAPITestCase(unittest.TestCase):
    def setUp(self):
        """Configurar ambiente de teste"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Criar tabelas
        db.create_all()
        
        # Criar usuário de teste
        import bcrypt
        password_hash = bcrypt.hashpw('password'.encode('utf-8'), bcrypt.gensalt())
        test_user = User(
            username='testuser',
            password_hash=password_hash,
            role='Administrador'
        )
        db.session.add(test_user)
        db.session.commit()

    def tearDown(self):
        """Limpar ambiente de teste"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_health_check(self):
        """Testar endpoint de health check"""
        response = self.app.get('/api/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)
        self.assertIn('version', data)

    def test_login_success(self):
        """Testar login com credenciais válidas"""
        response = self.app.post('/api/login',
                                data=json.dumps({
                                    'username': 'testuser',
                                    'password': 'password'
                                }),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('token', data)
        self.assertIn('user', data)
        self.assertEqual(data['user']['username'], 'testuser')

    def test_login_invalid_credentials(self):
        """Testar login com credenciais inválidas"""
        response = self.app.post('/api/login',
                                data=json.dumps({
                                    'username': 'testuser',
                                    'password': 'wrongpassword'
                                }),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 401)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('message', data)

    def test_login_missing_data(self):
        """Testar login sem dados obrigatórios"""
        response = self.app.post('/api/login',
                                data=json.dumps({}),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_get_cards(self):
        """Testar busca de cards"""
        # Criar card de teste
        test_card = Card(
            title='Test Card',
            description='Test Description',
            status='pending',
            priority='medium'
        )
        db.session.add(test_card)
        db.session.commit()
        
        response = self.app.get('/api/cards')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('cards', data)
        self.assertEqual(len(data['cards']), 1)
        self.assertEqual(data['cards'][0]['title'], 'Test Card')

    def test_create_card(self):
        """Testar criação de card"""
        card_data = {
            'title': 'New Test Card',
            'description': 'New Test Description',
            'status': 'pending',
            'priority': 'high'
        }
        
        response = self.app.post('/api/cards',
                                data=json.dumps(card_data),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('card', data)
        self.assertEqual(data['card']['title'], 'New Test Card')

    def test_create_card_missing_title(self):
        """Testar criação de card sem título"""
        card_data = {
            'description': 'Test Description'
        }
        
        response = self.app.post('/api/cards',
                                data=json.dumps(card_data),
                                content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_sla_metrics(self):
        """Testar endpoint de métricas SLA"""
        response = self.app.get('/api/sla')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        self.assertIn('metrics', data)
        self.assertIn('sla_targets', data['metrics'])
        self.assertIn('current_performance', data['metrics'])
        self.assertIn('deadlines', data['metrics'])

if __name__ == '__main__':
    unittest.main()

