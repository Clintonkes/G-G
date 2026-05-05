"""Verify pending properties after an inspection record exists.

Usage:
    python3 scripts/verify_inspected_properties.py
    python3 scripts/verify_inspected_properties.py --complete-inspections
"""

from __future__ import annotations

import argparse
from datetime import datetime

from sqlalchemy import select

from db.session import SessionLocal
from models.appointment import Appointment, AppointmentOutcome, AppointmentStatus
from models.notification import NotificationType
from models.property import Property, PropertyStatus
from services.notification_service import create_notification


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify pending properties that have inspection appointments.")
    parser.add_argument("--complete-inspections", action="store_true", help="Mark matching pending/confirmed inspection appointments as completed.")
    parser.add_argument("--dry-run", action="store_true", help="Preview records without writing changes.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        pending_properties = db.scalars(
            select(Property)
            .where(Property.status == PropertyStatus.PENDING_VERIFICATION, Property.is_verified.is_(False))
            .order_by(Property.created_at.asc())
        ).all()

        verified = 0
        skipped = 0
        for property_record in pending_properties:
            appointment = db.scalar(
                select(Appointment)
                .where(
                    Appointment.property_id == property_record.id,
                    Appointment.status.in_([AppointmentStatus.PENDING, AppointmentStatus.CONFIRMED, AppointmentStatus.COMPLETED]),
                )
                .order_by(Appointment.scheduled_date.desc())
            )
            if not appointment:
                skipped += 1
                print(f"skip: {property_record.title} ({property_record.id}) has no inspection appointment")
                continue

            verified += 1
            print(f"verify: {property_record.title} ({property_record.id}) via appointment {appointment.id}")
            if args.dry_run:
                continue

            if args.complete_inspections and appointment.status != AppointmentStatus.COMPLETED:
                appointment.status = AppointmentStatus.COMPLETED
                appointment.outcome = AppointmentOutcome.INTERESTED

            property_record.status = PropertyStatus.ACTIVE
            property_record.is_verified = True
            property_record.verified_at = datetime.utcnow()
            create_notification(
                db,
                property_record.landlord_id,
                "Listing verified",
                f"{property_record.title} has passed inspection and is now live in public search.",
                NotificationType.VERIFICATION,
            )

        if not args.dry_run:
            db.commit()

        print(f"verified={verified} skipped_no_inspection={skipped} pending_seen={len(pending_properties)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
