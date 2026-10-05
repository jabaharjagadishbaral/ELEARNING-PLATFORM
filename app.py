from flask import Flask

import db
import config as config_module
from config import Config


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)
    app.config["BASE_DIR"] = config_module.BASE_DIR

    db.init_app(app)

    with app.app_context():
        if app.config["DB_BACKEND"] == "sqlite":
            db.init_schema()

    from main import bp as main_bp
    from api import bp as api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)

    return app


if __name__ == "__main__":
    application = create_app()
    application.run(debug=True, host="0.0.0.0", port=5000)
