"""
Database layer — MS SQL Server via SQLAlchemy + pyodbc
Tables: incidents, violations, corrective_actions, cv_detections
"""
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Integer, Float,
    Boolean, DateTime, Text, ForeignKey, JSON
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.pool import QueuePool
import os, logging

logger = logging.getLogger(__name__)
Base = declarative_base()


# ── ORM Models ────────────────────────────────────────────────────────────────

class IncidentReport(Base):
    __tablename__ = "incident_reports"

    id            = Column(String(50), primary_key=True)   # INC-20250610-001
    incident_date = Column(DateTime, default=datetime.utcnow)
    location      = Column(String(200))
    reported_by   = Column(String(200))
    incident_type = Column(String(200))
    severity      = Column(String(20))   # CRITICAL / HIGH / MEDIUM / LOW
    description   = Column(Text)
    risk_score    = Column(Integer)
    compliance_status = Column(String(30))
    follow_up_required        = Column(Boolean, default=False)
    regulatory_notification   = Column(Boolean, default=False)
    notification_reason       = Column(Text)
    root_cause_immediate      = Column(Text)
    root_cause_root           = Column(Text)
    affected_personnel        = Column(Text)
    regulatory_references     = Column(JSON)   # ["OSHA 29 CFR 1910.132", ...]
    preventive_measures       = Column(JSON)
    annotated_image_b64       = Column(Text)   # base64 annotated image
    created_at = Column(DateTime, default=datetime.utcnow)

    violations         = relationship("Violation", back_populates="report",
                                      cascade="all, delete-orphan")
    corrective_actions = relationship("CorrectiveAction", back_populates="report",
                                      cascade="all, delete-orphan")
    cv_summary         = relationship("CVSummary", back_populates="report",
                                      uselist=False, cascade="all, delete-orphan")


class Violation(Base):
    __tablename__ = "violations"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    report_id        = Column(String(50), ForeignKey("incident_reports.id"))
    violation_id     = Column(String(20))    # V001, V002 …
    policy_reference = Column(String(50))
    violation_type   = Column(String(100))
    description      = Column(Text)
    severity         = Column(String(20))
    evidence         = Column(Text)
    immediate_action = Column(Boolean, default=False)

    report = relationship("IncidentReport", back_populates="violations")


class CorrectiveAction(Base):
    __tablename__ = "corrective_actions"

    id               = Column(Integer, primary_key=True, autoincrement=True)
    report_id        = Column(String(50), ForeignKey("incident_reports.id"))
    action_id        = Column(String(20))    # CA-001 …
    description      = Column(Text)
    priority         = Column(String(20))    # IMMEDIATE / SHORT_TERM / LONG_TERM
    responsible_party = Column(String(200))
    due_within       = Column(String(100))
    completed        = Column(Boolean, default=False)

    report = relationship("IncidentReport", back_populates="corrective_actions")


class CVSummary(Base):
    __tablename__ = "cv_summaries"

    id                = Column(Integer, primary_key=True, autoincrement=True)
    report_id         = Column(String(50), ForeignKey("incident_reports.id"))
    persons_detected  = Column(Integer, default=0)
    ppe_violations    = Column(Integer, default=0)
    hazard_count      = Column(Integer, default=0)
    total_detections  = Column(Integer, default=0)
    image_width       = Column(Integer)
    image_height      = Column(Integer)
    yolo_model        = Column(String(50))

    report = relationship("IncidentReport", back_populates="cv_summary")


# ── Database connection ───────────────────────────────────────────────────────

from sqlalchemy import create_engine, URL

def get_connection_string(database=None):
    server = os.getenv("MSSQL_SERVER", "sqlserver")
    port = os.getenv("MSSQL_PORT", "1433")

    if database is None:
        database = os.getenv("MSSQL_DATABASE", "ehs_db")

    user = os.getenv("MSSQL_USER", "sa")
    password = os.getenv("MSSQL_PASSWORD", "Temp123!")

    return URL.create(
        "mssql+pyodbc",
        username=user,
        password=password,
        host=server,
        port=int(port),
        database=database,
        query={
            "driver": "ODBC Driver 18 for SQL Server",
            "TrustServerCertificate": "yes",
        },
    )


def create_db_engine(database=None):
    conn_str = get_connection_string(database)
    return create_engine(
        conn_str,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,    # reconnect on stale connections
        echo=False
    )


def init_db(engine):
    """Create all tables if they don't exist."""
    Base.metadata.create_all(engine)
    logger.info("✅ Database tables created / verified")


# ── Repository (data access layer) ───────────────────────────────────────────

class ReportRepository:
    def __init__(self, session_factory):
        self.Session = session_factory

    def save(self, report_dict: dict, cv_results: dict, assessment: dict) -> str:
        """Persist a full incident report and all child records."""
        with self.Session() as session:
            report_id = report_dict.get("report_id",
                        f"INC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-001")

            incident = IncidentReport(
                id               = report_id,
                incident_date    = datetime.utcnow(),
                location         = report_dict.get("location"),
                reported_by      = report_dict.get("reported_by"),
                incident_type    = report_dict.get("incident_type"),
                severity         = report_dict.get("severity"),
                description      = report_dict.get("description"),
                risk_score       = assessment.get("risk_score", 0),
                compliance_status= assessment.get("overall_compliance_status"),
                follow_up_required      = report_dict.get("follow_up_required", False),
                regulatory_notification = report_dict.get("regulatory_notification_required", False),
                notification_reason     = report_dict.get("notification_reason"),
                root_cause_immediate    = report_dict.get("root_cause_analysis", {}).get("immediate_cause"),
                root_cause_root         = report_dict.get("root_cause_analysis", {}).get("root_cause"),
                affected_personnel      = report_dict.get("affected_personnel"),
                regulatory_references   = report_dict.get("regulatory_references", []),
                preventive_measures     = report_dict.get("preventive_measures", []),
                annotated_image_b64     = cv_results.get("annotated_image"),
            )

            # Violations
            for v in assessment.get("violations", []):
                incident.violations.append(Violation(
                    violation_id     = v.get("violation_id"),
                    policy_reference = v.get("policy_reference"),
                    violation_type   = v.get("violation_type"),
                    description      = v.get("description"),
                    severity         = v.get("severity"),
                    evidence         = v.get("evidence"),
                    immediate_action = v.get("immediate_action_required", False),
                ))

            # Corrective actions
            for ca in report_dict.get("corrective_actions", []):
                incident.corrective_actions.append(CorrectiveAction(
                    action_id         = ca.get("action_id"),
                    description       = ca.get("description"),
                    priority          = ca.get("priority"),
                    responsible_party = ca.get("responsible_party"),
                    due_within        = ca.get("due_within"),
                ))

            # CV summary
            summary = cv_results.get("summary", {})
            incident.cv_summary = CVSummary(
                persons_detected = summary.get("persons_in_frame", 0),
                ppe_violations   = summary.get("ppe_violations", 0),
                hazard_count     = summary.get("hazard_count", 0),
                total_detections = cv_results.get("total_detections", 0),
                image_width      = cv_results.get("image_dimensions", {}).get("width"),
                image_height     = cv_results.get("image_dimensions", {}).get("height"),
                yolo_model       = "yolov8n",
            )

            session.merge(incident)   # upsert — safe to retry
            session.commit()
            logger.info(f"💾 Report saved to SQL Server: {report_id}")
            return report_id

    def list_all(self, limit: int = 100, severity: str = None) -> list[dict]:
        with self.Session() as session:
            q = session.query(IncidentReport).order_by(
                IncidentReport.incident_date.desc()
            )
            if severity:
                q = q.filter(IncidentReport.severity == severity.upper())
            return [self._to_summary(r) for r in q.limit(limit)]

    def get_by_id(self, report_id: str) -> dict | None:
        with self.Session() as session:
            r = session.query(IncidentReport).filter_by(id=report_id).first()
            return self._to_full(r) if r else None

    def delete(self, report_id: str) -> bool:
        with self.Session() as session:
            r = session.query(IncidentReport).filter_by(id=report_id).first()
            if not r:
                return False
            session.delete(r)
            session.commit()
            return True

    def stats(self) -> dict:
        with self.Session() as session:
            from sqlalchemy import func
            total = session.query(func.count(IncidentReport.id)).scalar()
            by_severity = dict(
                session.query(IncidentReport.severity,
                              func.count(IncidentReport.id))
                             .group_by(IncidentReport.severity).all()
            )
            return {"total_reports": total, "by_severity": by_severity}

    # ── helpers ──────────────────────────────────────────────────────────────

    def _to_summary(self, r: IncidentReport) -> dict:
        return {
            "report_id":       r.id,
            "incident_date":   r.incident_date.isoformat() if r.incident_date else None,
            "location":        r.location,
            "severity":        r.severity,
            "incident_type":   r.incident_type,
            "compliance_status": r.compliance_status,
            "follow_up_required": r.follow_up_required,
        }

    def _to_full(self, r: IncidentReport) -> dict:
        return {
            **self._to_summary(r),
            "description":           r.description,
            "risk_score":            r.risk_score,
            "regulatory_notification_required": r.regulatory_notification,
            "notification_reason":   r.notification_reason,
            "regulatory_references": r.regulatory_references or [],
            "preventive_measures":   r.preventive_measures or [],
            "root_cause_analysis": {
                "immediate_cause": r.root_cause_immediate,
                "root_cause":      r.root_cause_root,
            },
            "violations": [
                {
                    "violation_id":     v.violation_id,
                    "policy_reference": v.policy_reference,
                    "violation_type":   v.violation_type,
                    "description":      v.description,
                    "severity":         v.severity,
                    "evidence":         v.evidence,
                    "immediate_action_required": v.immediate_action,
                }
                for v in r.violations
            ],
            "corrective_actions": [
                {
                    "action_id":         ca.action_id,
                    "description":       ca.description,
                    "priority":          ca.priority,
                    "responsible_party": ca.responsible_party,
                    "due_within":        ca.due_within,
                    "completed":         ca.completed,
                }
                for ca in r.corrective_actions
            ],
            "cv_summary": {
                "persons_detected": r.cv_summary.persons_detected,
                "ppe_violations":   r.cv_summary.ppe_violations,
                "hazard_count":     r.cv_summary.hazard_count,
            } if r.cv_summary else {},
        }