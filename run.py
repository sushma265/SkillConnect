from app import create_app, socketio
from flasgger import Swagger

app = create_app()

# Swagger Configuration
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger_template = {
    "info": {
        "title": "SkillConnect API",
        "description": "API Documentation for SkillConnect Platform",
        "version": "1.0.0"
    }
}

Swagger(app, config=swagger_config, template=swagger_template)

if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=False,
        allow_unsafe_werkzeug=True
    )