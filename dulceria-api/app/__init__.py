from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from .routes.pricing import bp as pricing_bp
from .config import Config
from .extensions import db, migrate, jwt  
from .routes.admin_reports import bp as admin_reports_bp
from flasgger import Swagger
from .routes.site import bp as site_bp
from .routes.admin_users import bp as admin_users_bp

def create_app():
    load_dotenv()

    app = Flask(__name__)
    app.config.from_object(Config)

    
    CORS(
        app,
        resources={r"/api/*": {"origins": ["http://localhost:5173"]}}, #buscar forma de no dejarlo hardcodeado
    )
    swagger = Swagger(app, template={
        "swagger": "2.0",
        "info": {
            "title": "Dulcería Mayoreo API",
            "description": "API escolar (Flask + JWT + SQLite)",
            "version": "1.0.0"
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "Escribe: Bearer <token>"
            }
        }
    })


    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)  

    from .routes.products import bp as products_bp
    from .routes.customers import bp as customers_bp
    from .routes.orders import bp as orders_bp
    from .routes.auth import bp as auth_bp  

    app.register_blueprint(products_bp)
    app.register_blueprint(customers_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(auth_bp)  
    app.register_blueprint(pricing_bp)
    app.register_blueprint(admin_reports_bp)
    app.register_blueprint(site_bp)
    app.register_blueprint(admin_users_bp)
    
    @app.get("/health")
    def health():
        return jsonify({"ok": True, "service": "dulceria-api"})

    @app.errorhandler(404)
    def not_found(_):
        return jsonify({"error": "Ruta no encontrada"}), 404

    return app
