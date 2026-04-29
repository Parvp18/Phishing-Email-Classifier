"""
PhishGuard Database Models
===========================
SQLAlchemy ORM models for persisting scan results and user feedback.
Uses SQLite as the backing store.
"""

import uuid
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _generate_uuid() -> str:
    """Return a new UUID4 string for use as a primary key."""
    return str(uuid.uuid4())


class ScanResult(db.Model):
    """Stores every email scan performed by the system."""

    __tablename__ = "scan_results"

    id: str = db.Column(
        db.String(36), primary_key=True, default=_generate_uuid
    )
    email_hash: str = db.Column(db.String(64), index=True, nullable=False)
    label: str = db.Column(db.String(16), nullable=False)
    confidence: float = db.Column(db.Float, nullable=False)
    risk_score: float = db.Column(db.Float, nullable=False)
    risk_level: str = db.Column(db.String(16), nullable=False)
    attack_type: str = db.Column(db.String(64), nullable=True)
    features_json: str = db.Column(db.Text, nullable=True)
    urls_json: str = db.Column(db.Text, nullable=True)
    shap_json: str = db.Column(db.Text, nullable=True)
    model_votes_json: str = db.Column(db.Text, nullable=True)
    word_heatmap_json: str = db.Column(db.Text, nullable=True)
    recommendation: str = db.Column(db.Text, nullable=True)
    sender: str = db.Column(db.String(256), nullable=True)
    subject: str = db.Column(db.String(512), nullable=True)
    email_body: str = db.Column(db.Text, nullable=True)
    scan_source: str = db.Column(db.String(16), nullable=False, default="paste")
    analysis_time_ms: float = db.Column(db.Float, nullable=True)
    created_at: datetime = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    feedbacks = db.relationship(
        "Feedback", backref="scan_result", lazy=True,
        cascade="all, delete-orphan"
    )

    def to_dict(self) -> dict:
        """Serialize the record to a plain dictionary."""
        import json
        return {
            "id": self.id,
            "email_hash": self.email_hash,
            "label": self.label,
            "confidence": self.confidence,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "attack_type": self.attack_type,
            "features": json.loads(self.features_json) if self.features_json else {},
            "urls_found": json.loads(self.urls_json) if self.urls_json else [],
            "shap_top_features": json.loads(self.shap_json) if self.shap_json else [],
            "model_votes": json.loads(self.model_votes_json) if self.model_votes_json else {},
            "word_heatmap": json.loads(self.word_heatmap_json) if self.word_heatmap_json else [],
            "recommendation": self.recommendation,
            "sender": self.sender,
            "subject": self.subject,
            "scan_source": self.scan_source,
            "analysis_time_ms": self.analysis_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Feedback(db.Model):
    """User-supplied corrections linked to a prior scan."""

    __tablename__ = "feedbacks"

    id: str = db.Column(
        db.String(36), primary_key=True, default=_generate_uuid
    )
    scan_id: str = db.Column(
        db.String(36), db.ForeignKey("scan_results.id"), nullable=False, index=True
    )
    correct_label: int = db.Column(db.Integer, nullable=False)
    created_at: datetime = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        """Serialize the record to a plain dictionary."""
        return {
            "id": self.id,
            "scan_id": self.scan_id,
            "correct_label": self.correct_label,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
