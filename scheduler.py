from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from models import db, Client, EmailLog
from email_service import send_reminder_email
import config


def send_pending_reminders(app):
    """Envía correos de recordatorio a clientes pendientes de pago."""
    with app.app_context():
        # Clientes que no han pagado y tienen email
        clients = Client.query.filter(
            Client.pagado == False,
            Client.email != '',
            Client.email.isnot(None),
        ).all()

        sent = 0
        errors = 0

        for client in clients:
            # Verificar si ya se envió correo en los últimos 3 días
            last_email = EmailLog.query.filter_by(
                client_id=client.id,
                estado_envio='enviado'
            ).order_by(EmailLog.fecha_envio.desc()).first()

            if last_email:
                days_since = (datetime.utcnow() - last_email.fecha_envio).days
                if days_since < config.EMAIL_INTERVAL_DAYS:
                    continue

            # Enviar correo
            success, detail = send_reminder_email(client)

            # Registrar en log
            log = EmailLog(
                client_id=client.id,
                tipo='recordatorio',
                estado_envio='enviado' if success else 'error',
                detalle=detail,
            )
            db.session.add(log)

            if success:
                sent += 1
            else:
                errors += 1

        db.session.commit()
        print(f"[Scheduler] {datetime.now().strftime('%Y-%m-%d %H:%M')} - Enviados: {sent}, Errores: {errors}")


def init_scheduler(app):
    """Inicializa el scheduler de tareas programadas."""
    scheduler = BackgroundScheduler()

    # Ejecutar cada 3 días
    scheduler.add_job(
        func=send_pending_reminders,
        trigger='interval',
        days=config.EMAIL_INTERVAL_DAYS,
        args=[app],
        id='send_reminders',
        name='Enviar recordatorios de pago',
        replace_existing=True,
    )

    scheduler.start()
    print(f"[Scheduler] Iniciado. Correos se enviarán cada {config.EMAIL_INTERVAL_DAYS} dias.")

    return scheduler
