from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Client(db.Model):
    __tablename__ = 'clients'

    id = db.Column(db.Integer, primary_key=True)
    nit = db.Column(db.String(50), index=True)
    dig_ver = db.Column(db.Integer)
    cobrador = db.Column(db.String(100))
    centro_costo = db.Column(db.String(100))
    subcentro_costo = db.Column(db.String(100))
    tercero = db.Column(db.String(50))
    sucursal = db.Column(db.Integer, default=0)
    nombre = db.Column(db.String(200), index=True)
    cuenta = db.Column(db.String(100))
    cta = db.Column(db.String(20))
    descripcion = db.Column(db.String(300))
    saldo = db.Column(db.Float, default=0)
    valor_vencido = db.Column(db.Float, default=0)
    telefono_1 = db.Column(db.String(30))
    telefono_2 = db.Column(db.String(30))
    ciudad = db.Column(db.String(100))
    comprobante = db.Column(db.String(50))
    fecha_factura = db.Column(db.Date)
    fecha_vencimiento = db.Column(db.Date)
    rango_360 = db.Column(db.Float, default=0)
    rango_359_91 = db.Column(db.Float, default=0)
    rango_90_60 = db.Column(db.Float, default=0)
    rango_59_30 = db.Column(db.Float, default=0)
    rango_29 = db.Column(db.Float, default=0)
    total = db.Column(db.Float, default=0)
    estado = db.Column(db.String(20), default='No Vencido')
    email = db.Column(db.String(200))
    pagado = db.Column(db.Boolean, default=False)
    fecha_pago = db.Column(db.Date, nullable=True)
    archivo_origen = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    email_logs = db.relationship('EmailLog', backref='client', lazy=True)

    @property
    def dias_para_vencer(self):
        if not self.fecha_vencimiento:
            return None
        return (self.fecha_vencimiento - date.today()).days

    @property
    def semaforo(self):
        if self.pagado:
            return 'pagado'
        dias = self.dias_para_vencer
        if dias is None:
            return 'sin_fecha'
        if dias < 0:
            return 'rojo'
        elif dias <= 30:
            return 'amarillo'
        else:
            return 'verde'

    def to_dict(self):
        return {
            'id': self.id,
            'nit': self.nit,
            'nombre': self.nombre,
            'ciudad': self.ciudad,
            'total': self.total,
            'fecha_vencimiento': self.fecha_vencimiento.isoformat() if self.fecha_vencimiento else None,
            'dias_para_vencer': self.dias_para_vencer,
            'semaforo': self.semaforo,
            'estado': self.estado,
            'email': self.email,
            'pagado': self.pagado,
            'fecha_pago': self.fecha_pago.isoformat() if self.fecha_pago else None,
            'comprobante': self.comprobante,
            'telefono_1': self.telefono_1,
            'telefono_2': self.telefono_2,
            'cobrador': self.cobrador,
            'centro_costo': self.centro_costo,
            'cuenta': self.cuenta,
            'descripcion': self.descripcion,
        }


class EmailLog(db.Model):
    __tablename__ = 'email_log'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(50), default='recordatorio')
    estado_envio = db.Column(db.String(20), default='enviado')
    detalle = db.Column(db.Text, nullable=True)
