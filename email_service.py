import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import config


def build_email_body(client):
    """Construye el cuerpo HTML del correo de recordatorio."""
    fecha_venc = client.fecha_vencimiento.strftime('%d/%m/%Y') if client.fecha_vencimiento else 'N/A'
    total_fmt = f"${client.total:,.2f}"

    estado_color = '#dc3545'  # rojo por defecto
    estado_texto = 'VENCIDO'
    if client.semaforo == 'amarillo':
        estado_color = '#ffc107'
        estado_texto = 'PROXIMO A VENCER'
    elif client.semaforo == 'verde':
        estado_color = '#198754'
        estado_texto = 'VIGENTE'

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
            <div style="background-color: #1a1a2e; color: white; padding: 20px; text-align: center;">
                <h2 style="margin: 0;">Centro Nacional de Consultoria S.A.</h2>
                <p style="margin: 5px 0 0 0;">Recordatorio de Pago</p>
            </div>

            <div style="padding: 25px;">
                <p>Estimado(a) <strong>{client.nombre}</strong>,</p>

                <p>Le recordamos que tiene una obligacion pendiente con el Centro Nacional de Consultoria S.A.
                A continuacion encontrara los detalles:</p>

                <table style="width: 100%; border-collapse: collapse; margin: 15px 0;">
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa;"><strong>NIT</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{client.nit}-{client.dig_ver}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa;"><strong>Comprobante</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{client.comprobante}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa;"><strong>Valor a Pagar</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; font-size: 1.1em; color: #dc3545;">{total_fmt}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa;"><strong>Fecha de Vencimiento</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{fecha_venc}</td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa;"><strong>Estado</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">
                            <span style="background-color: {estado_color}; color: white; padding: 3px 10px; border-radius: 4px;">
                                {estado_texto}
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 8px; border: 1px solid #ddd; background: #f8f9fa;"><strong>Descripcion</strong></td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{client.descripcion}</td>
                    </tr>
                </table>

                <p>Le solicitamos amablemente realizar el pago correspondiente a la mayor brevedad posible.
                Si ya realizo el pago, por favor ignore este mensaje.</p>

                <p>Para cualquier consulta, no dude en comunicarse con nosotros.</p>

                <p>Atentamente,<br>
                <strong>Departamento de Cartera</strong><br>
                Centro Nacional de Consultoria S.A.</p>
            </div>

            <div style="background-color: #f8f9fa; padding: 15px; text-align: center; font-size: 0.85em; color: #666;">
                Este es un mensaje automatico. Por favor no responda a este correo.
            </div>
        </div>
    </body>
    </html>
    """
    return html


def send_reminder_email(client):
    """Envía un correo de recordatorio a un cliente."""
    if not client.email:
        return False, "Cliente sin email registrado"

    if not config.SMTP_USER or not config.SMTP_PASSWORD:
        return False, "SMTP no configurado"

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Recordatorio de Pago - CNC - {client.comprobante}'
        msg['From'] = config.SMTP_FROM or config.SMTP_USER
        msg['To'] = client.email

        html_body = build_email_body(client)
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.sendmail(msg['From'], [client.email], msg.as_string())

        return True, "Enviado exitosamente"

    except Exception as e:
        return False, str(e)
