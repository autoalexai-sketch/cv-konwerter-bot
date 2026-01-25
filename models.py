"""
Database models for CV Konwerter
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class User(db.Model):
    """Пользователь Premium"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_premium = db.Column(db.Boolean, default=False)
    premium_expires = db.Column(db.DateTime, nullable=True)
    
    # Связь с CV
    cvs = db.relationship('CV', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.email}>'


class CV(db.Model):
    """Сохранённое резюме пользователя"""
    __tablename__ = 'cvs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Личные данные
    imie = db.Column(db.String(100), nullable=False)
    nazwisko = db.Column(db.String(100), nullable=False)
    telefon = db.Column(db.String(20), nullable=False)
    miasto = db.Column(db.String(100), nullable=False)
    stanowisko = db.Column(db.String(200))
    o_sobie = db.Column(db.Text)
    
    # JSON поля для сложных данных
    doswiadczenie = db.Column(db.Text)  # JSON array
    wyksztalcenie = db.Column(db.Text)  # JSON array
    umiejetnosci = db.Column(db.Text)   # JSON array
    jezyki = db.Column(db.Text)         # JSON array
    zainteresowania = db.Column(db.Text)  # JSON array
    
    # Метаданные
    template = db.Column(db.String(50), default='klasyczny')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Конвертация в словарь для генератора CV"""
        return {
            'imie': self.imie,
            'nazwisko': self.nazwisko,
            'email': self.user.email,
            'telefon': self.telefon,
            'miasto': self.miasto,
            'stanowisko': self.stanowisko,
            'o_sobie': self.o_sobie,
            'doswiadczenie': json.loads(self.doswiadczenie) if self.doswiadczenie else [],
            'wyksztalcenie': json.loads(self.wyksztalcenie) if self.wyksztalcenie else [],
            'umiejetnosci': json.loads(self.umiejetnosci) if self.umiejetnosci else [],
            'jezyki': json.loads(self.jezyki) if self.jezyki else [],
            'zainteresowania': json.loads(self.zainteresowania) if self.zainteresowania else []
        }
    
    def __repr__(self):
        return f'<CV {self.imie} {self.nazwisko}>'


class Payment(db.Model):
    """История платежей"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Przelewy24 данные
    session_id = db.Column(db.String(100), unique=True)
    order_id = db.Column(db.String(100))
    amount = db.Column(db.Integer, default=3900)  # 39.00 PLN в groszach
    currency = db.Column(db.String(3), default='PLN')
    status = db.Column(db.String(50), default='pending')  # pending, completed, failed
    
    # Метаданные
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Связь с пользователем
    user = db.relationship('User', backref='payments')
    
    def __repr__(self):
        return f'<Payment {self.order_id} - {self.status}>'
