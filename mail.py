"""
from flask import Flask
from flask_mail import Mail, Message
import os

app = Flask(__name__)

# Configuración del servidor SMTP
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = os.environ.get('MAIL_PORT')
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL')
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME_2')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
mail = Mail(app)

@app.route("/")
def index():
    msg = Message(subject='Testing Flask Mail',
                  sender=app.config['MAIL_USERNAME'],
                  recipients=['proyectogipsy@gmail.com', 'yarimacontreras.ucv@gmail.com'])
    msg.body = "Prueba de envío de correo desde Aplicación de Recibo"
    mail.send(msg)
    return "Message sent!"

if __name__ == '__main__':
    app.run()
"""