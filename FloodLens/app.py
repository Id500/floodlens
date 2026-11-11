import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory, flash, redirect, url_for
from werkzeug.utils import secure_filename

from config import Config
from models import db
from models.report import FloodReport
from modules.weather import fetch_weather_data
from modules.flood_api import fetch_river_discharge
from modules.nasa import get_satellite_metadata, get_default_imagery_date, GIBS_LAYERS
from modules.risk_engine import calculate_flood_risk
from modules.image_analysis import analyze_satellite_image
from modules.map_service import PRESET_LOCATIONS, search_location

def create_app(config_class=Config):
    """Application factory for FloodLens."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Ensure upload & instance folders exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['INSTANCE_DIR'], exist_ok=True)

    # Create tables & initial seed data
    with app.app_context():
        db.create_all()
        _seed_initial_reports()

    # Register routes
    _register_page_routes(app)
    _register_api_routes(app)
    _register_error_handlers(app)

    return app

def _seed_initial_reports():
    """Seed sample unverified community flood reports for Chennai if database is empty."""
    if FloodReport.query.count() == 0:
        samples = [
            FloodReport(
                location_name="Velachery Main Road & 100ft Inner Ring Rd, Chennai",
                latitude=12.9815,
                longitude=80.2180,
                severity="Severe",
                water_depth="Knee deep (15-50cm)",
                description="Heavy inundation near AGS Cinemas junction. Stagnant runoff 1.5 feet deep. Two-wheelers stalled.",
                reporter_name="Citizen Observation",
                status="Unverified",
                created_at=datetime.now(timezone.utc)
            ),
            FloodReport(
                location_name="Mudichur Lake Surplus Canal, Chennai Outskirts",
                latitude=12.9180,
                longitude=80.0760,
                severity="Moderate",
                water_depth="Ankle deep (< 15cm)",
                description="Canal outflow approaching culvert crown. Water spreading into service lanes. Municipal pumps active.",
                reporter_name="Ward Volunteer",
                status="Unverified",
                created_at=datetime.now(timezone.utc)
            ),
            FloodReport(
                location_name="Perumbakkam Lowlands, Chennai",
                latitude=12.9035,
                longitude=80.1942,
                severity="Critical",
                water_depth="Waist deep (50-100cm)",
                description="Severe backflow from marshland. Ground floors in low-elevation tenements flooded. Emergency boats deployed.",
                reporter_name="Community First Responder",
                status="Unverified",
                created_at=datetime.now(timezone.utc)
            )
        ]
        db.session.bulk_save_objects(samples)
        db.session.commit()

def _allowed_file(filename: str) -> bool:
    """Validate file extension for security."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS

# -------------------------------------------------------------
# PAGE ROUTES
# -------------------------------------------------------------
def _register_page_routes(app: Flask):

    @app.context_processor
    def inject_common_context():
        """Expose default location and presets to all Jinja templates."""
        return {
            'default_lat': Config.DEFAULT_LAT,
            'default_lon': Config.DEFAULT_LON,
            'default_location_name': Config.DEFAULT_LOCATION_NAME,
            'preset_locations': PRESET_LOCATIONS,
            'current_year': datetime.now(timezone.utc).year,
            'active_date': get_default_imagery_date()
        }

    @app.route('/')
    def index():
        """Overview dashboard page."""
        return render_template('index.html', page_id='overview')

    @app.route('/weather')
    def weather_page():
        """Weather Intelligence page."""
        return render_template('dashboard.html', page_id='weather')

    @app.route('/satellite')
    def satellite_page():
        """NASA Satellite Imagery page."""
        meta = get_satellite_metadata()
        return render_template('satellite.html', page_id='satellite', metadata=meta)

    @app.route('/risk')
    def risk_page():
        """Explainable Flood Risk Analysis page."""
        return render_template('risk.html', page_id='risk')

    @app.route('/river')
    def river_page():
        """River Discharge page."""
        return render_template('river.html', page_id='river')

    @app.route('/analysis')
    def analysis_page():
        """Satellite Image Analysis (OpenCV) page."""
        return render_template('analysis.html', page_id='analysis')

    @app.route('/map')
    def map_page():
        """Full interactive flood map."""
        return render_template('map.html', page_id='map')

    @app.route('/reports')
    def reports_page():
        """Community flood reports page."""
        reports = FloodReport.query.order_by(FloodReport.created_at.desc()).all()
        return render_template('reports.html', page_id='reports', reports=[r.to_dict() for r in reports])

    @app.route('/about')
    def about_page():
        """Methodology and disclaimers page."""
        return render_template('about.html', page_id='about')

    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        """Serve processed or uploaded images safely."""
        return send_from_directory(Config.UPLOAD_FOLDER, filename)

# -------------------------------------------------------------
# REST API ENDPOINTS
# -------------------------------------------------------------
def _register_api_routes(app: Flask):

    @app.route('/api/weather', methods=['GET'])
    def api_weather():
        """Fetch meteorological metrics for latitude and longitude."""
        try:
            lat = float(request.args.get('lat', Config.DEFAULT_LAT))
            lon = float(request.args.get('lon', Config.DEFAULT_LON))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Invalid latitude or longitude'}), 400

        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return jsonify({'success': False, 'error': 'Coordinates out of valid geographical bounds'}), 400

        try:
            data = fetch_weather_data(lat, lon, timeout=Config.API_TIMEOUT)
            return jsonify({'success': True, 'data': data}), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 502

    @app.route('/api/flood', methods=['GET'])
    def api_flood():
        """Fetch GloFAS river discharge metrics."""
        try:
            lat = float(request.args.get('lat', Config.DEFAULT_LAT))
            lon = float(request.args.get('lon', Config.DEFAULT_LON))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Invalid latitude or longitude'}), 400

        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return jsonify({'success': False, 'error': 'Coordinates out of bounds'}), 400

        try:
            data = fetch_river_discharge(lat, lon, timeout=Config.API_TIMEOUT)
            return jsonify({'success': True, 'data': data}), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 502

    @app.route('/api/satellite', methods=['GET'])
    def api_satellite():
        """Fetch NASA GIBS layer metadata and WMTS tile configuration."""
        layer = request.args.get('layer', 'MODIS_Terra_CorrectedReflectance_Bands721')
        date_str = request.args.get('date', get_default_imagery_date())
        meta = get_satellite_metadata(layer, date_str)
        return jsonify({'success': True, 'data': meta}), 200

    @app.route('/api/risk', methods=['GET'])
    def api_risk():
        """Calculate multi-factor explainable flood risk score."""
        try:
            lat = float(request.args.get('lat', Config.DEFAULT_LAT))
            lon = float(request.args.get('lon', Config.DEFAULT_LON))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Invalid coordinates'}), 400

        try:
            weather_data = fetch_weather_data(lat, lon, timeout=Config.API_TIMEOUT)
            flood_data = fetch_river_discharge(lat, lon, timeout=Config.API_TIMEOUT)
            risk = calculate_flood_risk(weather_data, flood_data)
            return jsonify({
                'success': True,
                'coordinates': {'latitude': lat, 'longitude': lon},
                'data': risk
            }), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/api/reports', methods=['GET'])
    def api_get_reports():
        """Fetch community flood reports with optional severity filtering."""
        severity = request.args.get('severity')
        limit = request.args.get('limit', 100, type=int)

        query = FloodReport.query
        if severity and severity.lower() != 'all':
            query = query.filter(FloodReport.severity.ilike(severity))

        reports = query.order_by(FloodReport.created_at.desc()).limit(limit).all()
        return jsonify({
            'success': True,
            'count': len(reports),
            'reports': [r.to_dict() for r in reports]
        }), 200

    @app.route('/api/reports', methods=['POST'])
    def api_post_report():
        """Submit a community flood report."""
        data = request.form if request.form else (request.get_json() or {})

        location_name = data.get('location_name', '').strip()
        description = data.get('description', '').strip()
        severity = data.get('severity', 'Moderate').strip()
        water_depth = data.get('water_depth', 'Not specified').strip()
        reporter_name = data.get('reporter_name', 'Anonymous Citizen').strip()

        try:
            lat = float(data.get('latitude'))
            lon = float(data.get('longitude'))
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Valid latitude and longitude are required'}), 400

        if not location_name or len(location_name) < 3:
            return jsonify({'success': False, 'error': 'Location name must be at least 3 characters'}), 400

        if not description or len(description) < 5:
            return jsonify({'success': False, 'error': 'Please provide a clear description of at least 5 characters'}), 400

        if severity not in ['Minor', 'Moderate', 'Severe', 'Critical']:
            severity = 'Moderate'

        # Optional image upload
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename and _allowed_file(file.filename):
                safe_name = f"report_{uuid.uuid4().hex[:8]}_{secure_filename(file.filename)}"
                file_path = os.path.join(Config.UPLOAD_FOLDER, safe_name)
                file.save(file_path)
                image_filename = safe_name

        report = FloodReport(
            location_name=location_name,
            latitude=lat,
            longitude=lon,
            severity=severity,
            water_depth=water_depth,
            description=description,
            reporter_name=reporter_name or 'Anonymous Citizen',
            status='Unverified',
            image_filename=image_filename,
            created_at=datetime.now(timezone.utc)
        )

        db.session.add(report)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Report submitted successfully. Labeled as unverified until reviewed.',
            'report': report.to_dict()
        }), 201

    @app.route('/api/analyze-image', methods=['POST'])
    def api_analyze_image():
        """OpenCV satellite/aerial image analysis endpoint."""
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image file uploaded'}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No selected image file'}), 400

        if not _allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Unsupported file format. Please upload JPG, PNG, or TIFF.'}), 400

        try:
            unique_id = uuid.uuid4().hex[:8]
            safe_original_name = f"sat_{unique_id}_{secure_filename(file.filename)}"
            original_path = os.path.join(Config.UPLOAD_FOLDER, safe_original_name)
            file.save(original_path)

            output_name = f"processed_{safe_original_name}"
            output_path = os.path.join(Config.UPLOAD_FOLDER, output_name)

            # Run OpenCV segmentation & analysis
            result = analyze_satellite_image(original_path, output_path)
            result['original_image_filename'] = safe_original_name
            result['processed_image_url'] = url_for('uploaded_file', filename=output_name)
            result['original_image_url'] = url_for('uploaded_file', filename=safe_original_name)

            return jsonify(result), 200
        except Exception as e:
            return jsonify({'success': False, 'error': f"Image analysis failed: {str(e)}"}), 500

    @app.route('/api/geocode', methods=['GET'])
    def api_geocode():
        """Search locations globally via OpenStreetMap Nominatim."""
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'success': True, 'results': []})
        results = search_location(query)
        return jsonify({'success': True, 'results': results})

    @app.route('/api/presets', methods=['GET'])
    def api_presets():
        """Return preset flood monitoring regions."""
        return jsonify({'success': True, 'presets': PRESET_LOCATIONS})

# -------------------------------------------------------------
# ERROR HANDLERS
# -------------------------------------------------------------
def _register_error_handlers(app: Flask):

    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': 'Resource not found'}), 404
        return render_template('base.html', page_id='error', error_title='404 - Page Not Found',
                               error_msg='The requested page does not exist.'), 404

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return jsonify({'success': False, 'error': 'File exceeds maximum upload limit of 16MB'}), 413

    @app.errorhandler(500)
    def internal_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': 'Internal system error'}), 500
        return render_template('base.html', page_id='error', error_title='500 - Server Error',
                               error_msg='An unexpected server error occurred.'), 500

# Standalone execution
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
