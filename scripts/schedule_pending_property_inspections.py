"""Schedule inspection appointments for pending property listings.

Usage:
    python3 scripts/schedule_pending_property_inspections.py --date 2026-05-10T10:00
"""

from __future__ import annotations

import argparse
from datetime import datetime

from sqlalchemy import select

from db.session import SessionLocal
from models.appointment import Appointment, AppointmentStatus
from models.notification import NotificationType
from models.property import Property, PropertyStatus
from services.helpers import generate_id
from services.notification_service import create_notification


def parse_date(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use ISO format, for example 2026-05-10T10:00") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Create inspection appointments for pending property listings.")
    parser.add_argument("--date", required=True, type=parse_date, help="Inspection date/time in ISO format.")
    parser.add_argument("--notes", default="Admin inspection scheduled before verification.", help="Appointment note.")
    parser.add_argument("--dry-run", action="store_true", help="Preview records without writing changes.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        pending_properties = db.scalars(
            select(Property)
            .where(Property.status == PropertyStatus.PENDING_VERIFICATION, Property.is_verified.is_(False))
            .order_by(Property.created_at.asc())
        ).all()

        created = 0
        skipped = 0
        for property_record in pending_properties:
            existing = db.scalar(
                select(Appointment).where(
                    Appointment.property_id == property_record.id,
                    Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED]),
                )
            )
            if existing:
                skipped += 1
                continue

            created += 1
            print(f"schedule: {property_record.title} ({property_record.id}) for {args.date.isoformat()}")
            if args.dry_run:
                continue

            appointment = Appointment(
                id=generate_id(),
                tenant_id=property_record.landlord_id,
                landlord_id=property_record.landlord_id,
                property_id=property_record.id,
                scheduled_date=args.date,
                tenant_notes=args.notes,
            )
            db.add(appointment)
            create_notification(
                db,
                property_record.landlord_id,
                "Inspection appointment scheduled",
                f"Inspection for {property_record.title} has been scheduled for {args.date.strftime('%b %d, %Y %I:%M %p')}.",
                NotificationType.APPOINTMENT,
            )

        if not args.dry_run:
            db.commit()

        print(f"created={created} skipped_existing={skipped} pending_seen={len(pending_properties)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
