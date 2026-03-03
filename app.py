import os
from datetime import date, datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from models import db, Client, EmailLog
from excel_loader import load_excel
import config

app = Flask(__name__)
app.config.from_object(config)

# Asegurar carpeta de uploads
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db.init_app(app)

with app.app_context():
    db.create_all()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


def get_dashboard_stats():
    """Calcula estadísticas para el dashboard."""
    today = date.today()
    clients = Client.query.filter_by(pagado=False).all()

    stats = {
        'total': len(clients),
        'vencidos': 0, 'monto_vencidos': 0,
        'por_vencer': 0, 'monto_por_vencer': 0,
        'al_dia': 0, 'monto_al_dia': 0,
        'pagados': 0, 'monto_pagados': 0,
        'monto_total': 0,
    }

    for c in clients:
        stats['monto_total'] += c.total
        sem = c.semaforo
        if sem == 'rojo':
            stats['vencidos'] += 1
            stats['monto_vencidos'] += c.total
        elif sem == 'amarillo':
            stats['por_vencer'] += 1
            stats['monto_por_vencer'] += c.total
        elif sem == 'verde':
            stats['al_dia'] += 1
            stats['monto_al_dia'] += c.total

    pagados = Client.query.filter_by(pagado=True).all()
    stats['pagados'] = len(pagados)
    stats['monto_pagados'] = sum(c.total for c in pagados)

    return stats


def get_filtered_clients(filtro, buscar=None):
    """Retorna clientes según el filtro y búsqueda aplicados."""
    today = date.today()
    from datetime import timedelta

    # Query base según filtro
    if filtro == 'rojo':
        query = Client.query.filter(
            Client.pagado == False,
            Client.fecha_vencimiento < today
        )
    elif filtro == 'amarillo':
        limite = today + timedelta(days=30)
        query = Client.query.filter(
            Client.pagado == False,
            Client.fecha_vencimiento >= today,
            Client.fecha_vencimiento <= limite
        )
    elif filtro == 'verde':
        limite = today + timedelta(days=30)
        query = Client.query.filter(
            Client.pagado == False,
            Client.fecha_vencimiento > limite
        )
    elif filtro == 'pagado':
        query = Client.query.filter_by(pagado=True)
    else:
        query = Client.query

    # Aplicar búsqueda si existe
    if buscar and buscar.strip():
        buscar = buscar.strip()
        query = query.filter(
            db.or_(
                Client.nombre.ilike(f'%{buscar}%'),
                Client.nit.ilike(f'%{buscar}%'),
                Client.comprobante.ilike(f'%{buscar}%'),
                Client.ciudad.ilike(f'%{buscar}%'),
                Client.email.ilike(f'%{buscar}%'),
            )
        )

    return query.order_by(Client.fecha_vencimiento.asc()).all()


@app.route('/')
def dashboard():
    filtro = request.args.get('filtro', 'todos')
    buscar = request.args.get('buscar', '').strip()
    today = date.today()
    clients = get_filtered_clients(filtro, buscar)
    stats = get_dashboard_stats()
    return render_template('dashboard.html', clients=clients, stats=stats, filtro=filtro, buscar=buscar, today=today)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            result = load_excel(filepath, filename)

            if result['errors']:
                flash(f"Cargados {result['total']} registros ({result['added']} nuevos, {result['updated']} actualizados). Errores: {len(result['errors'])}", 'warning')
            else:
                flash(f"Cargados exitosamente {result['total']} registros ({result['added']} nuevos, {result['updated']} actualizados)", 'success')

            return redirect(url_for('dashboard'))
        else:
            flash('Tipo de archivo no permitido. Solo .xlsx o .xls', 'danger')
            return redirect(request.url)

    return render_template('upload.html')


@app.route('/search')
def search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])

    results = Client.query.filter(
        db.or_(
            Client.nombre.ilike(f'%{q}%'),
            Client.nit.ilike(f'%{q}%'),
            Client.comprobante.ilike(f'%{q}%'),
        )
    ).limit(20).all()

    return jsonify([c.to_dict() for c in results])


@app.route('/client/<int:client_id>')
def client_detail(client_id):
    client = Client.query.get_or_404(client_id)
    emails = EmailLog.query.filter_by(client_id=client_id).order_by(EmailLog.fecha_envio.desc()).all()
    return render_template('client_detail.html', client=client, emails=emails)


@app.route('/client/<int:client_id>/pay', methods=['POST'])
def mark_paid(client_id):
    client = Client.query.get_or_404(client_id)
    client.pagado = True
    client.fecha_pago = date.today()
    client.estado = 'Pagado'
    db.session.commit()
    flash(f'{client.nombre} marcado como pagado', 'success')
    return redirect(url_for('client_detail', client_id=client_id))


@app.route('/client/<int:client_id>/unpay', methods=['POST'])
def mark_unpaid(client_id):
    client = Client.query.get_or_404(client_id)
    client.pagado = False
    client.fecha_pago = None
    # Recalcular estado
    if client.fecha_vencimiento and client.fecha_vencimiento < date.today():
        client.estado = 'Vencido'
    else:
        client.estado = 'No Vencido'
    db.session.commit()
    flash(f'{client.nombre} marcado como no pagado', 'info')
    return redirect(url_for('client_detail', client_id=client_id))


@app.route('/client/<int:client_id>/update_email', methods=['POST'])
def update_email(client_id):
    client = Client.query.get_or_404(client_id)
    new_email = request.form.get('email', '').strip()
    client.email = new_email
    db.session.commit()
    flash(f'Email actualizado para {client.nombre}', 'success')
    return redirect(url_for('client_detail', client_id=client_id))


@app.route('/send_emails', methods=['POST'])
def send_emails():
    """Envía correos inmediatos a los clientes del filtro actual."""
    from email_service import send_reminder_email

    filtro = request.form.get('filtro', 'todos')
    buscar = request.form.get('buscar', '').strip()
    client_ids = request.form.getlist('client_ids')

    # Si se enviaron IDs específicos (selección manual), usar esos
    if client_ids:
        clients = Client.query.filter(Client.id.in_(client_ids)).all()
    else:
        # Sino, usar el filtro actual con búsqueda
        clients = get_filtered_clients(filtro, buscar)

    sent = 0
    errors = 0
    sin_email = 0

    for client in clients:
        if client.pagado:
            continue
        if not client.email or client.email.strip() == '':
            sin_email += 1
            continue

        success, detail = send_reminder_email(client)

        log = EmailLog(
            client_id=client.id,
            tipo='recordatorio_manual',
            estado_envio='enviado' if success else 'error',
            detalle=detail,
        )
        db.session.add(log)

        if success:
            sent += 1
        else:
            errors += 1

    db.session.commit()

    msg = f"Correos enviados: {sent}"
    if errors:
        msg += f" | Errores: {errors}"
    if sin_email:
        msg += f" | Sin email: {sin_email}"

    if errors:
        flash(msg, 'warning')
    else:
        flash(msg, 'success')

    return redirect(url_for('dashboard', filtro=filtro, buscar=buscar))


@app.route('/client/<int:client_id>/send_email', methods=['POST'])
def send_single_email(client_id):
    """Envía correo inmediato a un cliente individual."""
    from email_service import send_reminder_email

    client = Client.query.get_or_404(client_id)

    if not client.email or client.email.strip() == '':
        flash(f'El cliente {client.nombre} no tiene email registrado', 'danger')
        return redirect(url_for('client_detail', client_id=client_id))

    success, detail = send_reminder_email(client)

    log = EmailLog(
        client_id=client.id,
        tipo='recordatorio_manual',
        estado_envio='enviado' if success else 'error',
        detalle=detail,
    )
    db.session.add(log)
    db.session.commit()

    if success:
        flash(f'Correo enviado exitosamente a {client.email}', 'success')
    else:
        flash(f'Error al enviar correo: {detail}', 'danger')

    return redirect(url_for('client_detail', client_id=client_id))


@app.route('/emails')
def email_log():
    logs = EmailLog.query.order_by(EmailLog.fecha_envio.desc()).limit(200).all()
    return render_template('email_log.html', logs=logs)


@app.template_filter('currency')
def currency_filter(value):
    """Formatea un número como moneda colombiana."""
    try:
        return f"${value:,.2f}"
    except (ValueError, TypeError):
        return "$0.00"


@app.template_filter('date_format')
def date_format_filter(value):
    """Formatea una fecha."""
    if not value:
        return '-'
    if isinstance(value, str):
        return value
    return value.strftime('%d/%m/%Y')


if __name__ == '__main__':
    # Importar y arrancar el scheduler
    from scheduler import init_scheduler
    init_scheduler(app)

    app.run(debug=True, port=5000, host="0.0.0.0")
