from flask import Flask
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    with app.app_context():
        # Importar y registrar los blueprints
        from .routes import auth, backup, main, document, audit, dashboard, ayuda, configuracion
        
        app.register_blueprint(auth.bp)
        app.register_blueprint(backup.bp)
        app.register_blueprint(main.bp)
        app.register_blueprint(document.bp)
        app.register_blueprint(audit.bp)
        app.register_blueprint(dashboard.bp)
        app.register_blueprint(ayuda.bp)
        app.register_blueprint(configuracion.bp)
        
        return app
