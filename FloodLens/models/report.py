from datetime import datetime, timezone
from models import db

class FloodReport(db.Model):
    """Community flood incident report model."""
    __tablename__ = 'flood_reports'

    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(150), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    severity = db.Column(db.String(50), nullable=False, default='Moderate')  # Minor, Moderate, Severe, Critical
    water_depth = db.Column(db.String(50), nullable=True)  # Ankle deep, Knee deep, Waist deep, Submerged
    description = db.Column(db.Text, nullable=False)
    reporter_name = db.Column(db.String(100), default='Anonymous Citizen')
    status = db.Column(db.String(50), default='Unverified')  # Labeled as unverified until reviewed
    image_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        """Serialize report to dictionary."""
        return {
            'id': self.id,
            'location_name': self.location_name,
            'latitude': round(self.latitude, 5),
            'longitude': round(self.longitude, 5),
            'severity': self.severity,
            'water_depth': self.water_depth or 'Not specified',
            'description': self.description,
            'reporter_name': self.reporter_name or 'Anonymous Citizen',
            'status': self.status,
            'image_filename': self.image_filename,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S UTC') if self.created_at else None,
            'time_ago': self._format_time_ago()
        }

    def _format_time_ago(self):
        """Return human-readable time difference."""
        if not self.created_at:
            return 'Just now'
        # Normalize timezone
        now = datetime.now(timezone.utc)
        created = self.created_at
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        diff = now - created
        seconds = diff.total_seconds()
        if seconds < 60:
            return 'Just now'
        elif seconds < 3600:
            return f"{int(seconds // 60)} mins ago"
        elif seconds < 86400:
            return f"{int(seconds // 3600)} hours ago"
        else:
            return f"{int(seconds // 86400)} days ago"
