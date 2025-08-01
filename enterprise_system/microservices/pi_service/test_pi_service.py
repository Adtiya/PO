import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.profile import profile_bp
from src.routes.identity import identity_bp

print('Creating Flask app...')
app = Flask(__name__)
app.config['SECRET_KEY'] = 'pi-service-secret-key-change-in-production'

print('Setting up CORS...')
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])

print('Registering blueprints...')
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(profile_bp, url_prefix='/api')
app.register_blueprint(identity_bp, url_prefix='/api')

print('Setting up database...')
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'src', 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.route('/health')
def health_check():
    return jsonify({
        "service": "PI (Profile/Identity) Service",
        "status": "healthy",
        "version": "1.0.0"
    })

print('Creating database tables...')
with app.app_context():
    db.create_all()

print('Starting PI service on port 5001...')
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
