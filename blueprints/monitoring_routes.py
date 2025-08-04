from flask import Blueprint, jsonify

monitoring_bp = Blueprint('monitoring', __name__)

@monitoring_bp.route('/api/monitoring/health')
def monitoring_health():
    return jsonify({'status': 'ok', 'message': 'Monitoring route under construction'})
