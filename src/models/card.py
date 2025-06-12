from datetime import datetime
from src import db

class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ID_RC = db.Column(db.String(50), unique=True, nullable=False)
    Criado_Por = db.Column(db.String(120), nullable=False)
    Valor_Estimado = db.Column(db.Float, nullable=False)
    Status = db.Column(db.String(50), default='Solicitado')
    Tipo_Requisicao = db.Column(db.String(50), default='Padrão')
    Unidade = db.Column(db.String(100), default='Maracanaú')
    Fornecedor_Sugerido = db.Column(db.String(120), default='N/A')
    Data_Criacao = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "ID_RC": self.ID_RC,
            "Criado_Por": self.Criado_Por,
            "Valor_Estimado": self.Valor_Estimado,
            "Status": self.Status,
            "Tipo_Requisicao": self.Tipo_Requisicao,
            "Unidade": self.Unidade,
            "Fornecedor_Sugerido": self.Fornecedor_Sugerido,
            "Data_Criacao": self.Data_Criacao.isoformat() if self.Data_Criacao else None
        }