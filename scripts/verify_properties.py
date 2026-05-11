"""Verify pending property listings — admin tool until the admin panel ships.

Lists every property awaiting verification and lets you approve or reject individual
listings. Approved listings go ACTIVE and become searchable. Rejected listings are
set INACTIVE with a reason sent to the landlord's dashboard.

Usage:
  # List all properties pending verification
  python3 scripts/verify_properties.py

  # Approve a specific property (mark ACTIVE + verified)
  python3 scripts/verify_properties.py --approve <property_id>

  # Approve ALL pending properties at once
  python3 scripts/verify_properties.py --approve-all

  # Reject a property with a reason sent to the landlord
  python3 scripts/verify_properties.py --reject <property_id> --reason "Ownership documents unclear"

  # Preview any action without writing to the database
  python3 scripts/verify_properties.py --approve <id> --dry-run
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from db.session import SessionLocal
from models.notification import NotificationType
from models.property import Property, PropertyStatus
from models.user import User
from services.notification_service import create_notification


SEPARATOR = "-" * 90


def fmt_date(dt: datetime) -> str:
    return dt.strftime("%a, %d %b %Y  %I:%M %p UTC")


def print_property(prop: Property, index: int) -> None:
    landlord: User = prop.landlord
    days_waiting = (datetime.utcnow() - prop.created_at).days

    print(f"\n[{index}]  ID            : {prop.id}")
    print(f"     Title         : {prop.title}")
    print(f"     Type          : {prop.property_type.value}")
    print(f"     Location      : {prop.neighbourhood}, {prop.city}, {prop.state}")
    print(f"     Address       : {prop.address}")
    print(f"     Rent          : {prop.currency} {prop.annual_rent:,.0f}/yr")
    print(f"     Bedrooms      : {prop.bedrooms}   Bathrooms: {prop.bathrooms}   Toilets: {prop.toilets}")
    print(f"     Furnished     : {'Yes' if prop.is_furnished else 'No'}")
    if prop.amenities:
        print(f"     Amenities     : {', '.join(prop.amenities)}")
    print(f"     Photos        : {len(prop.photo_urls)} uploaded")
    print(f"     Videos        : {len(prop.video_urls)} uploaded")
    print(f"     Documents     : {len(prop.document_urls)} ownership doc(s)")
    print(f"     Submitted     : {fmt_date(prop.created_at)}  ({days_waiting}d ago)")
    print(f"     Landlord      : {landlord.full_name if landlord else '?'} <{landlord.email if landlord else '?'}>")
    if landlord:
        print(f"     Landlord ph.  : {landlord.phone_number or '-'}")
        print(f"     ID verified   : {'Yes' if landlord.id_verified else 'No'}")


def load_pending(db) -> list[Property]:
    return db.scalars(
        select(Property)
        .options(joinedload(Property.landlord))
        .where(Property.status == PropertyStatus.PENDING_VERIFICATION)
        .order_by(Property.created_at.asc())
    ).all()


def approve_property(db, prop: Property, dry_run: bool) -> None:
    landlord: User = prop.landlord
    landlord_name = landlord.full_name if landlord else "Landlord"

    print(f"\n  Approving: {prop.title} ({prop.id})")
    print(f"  Landlord : {landlord_name}")

    if dry_run:
        print("  DRY RUN — no changes written.")
        return

    prop.status = PropertyStatus.ACTIVE
    prop.is_verified = True
    prop.verified_at = datetime.utcnow()

    if landlord:
        create_notification(
            db,
            landlord.id,
            "Listing verified and live",
            f"Your property '{prop.title}' in {prop.neighbourhood}, {prop.city} has been "
            f"verified by G&G Homes admin and is now live in public search. Tenants can "
            f"browse and request inspections from your listing.",
            NotificationType.VERIFICATION,
        )

    print(f"  ✓ Approved — '{prop.title}' is now ACTIVE and searchable.")


def reject_property(db, prop: Property, reason: str, dry_run: bool) -> None:
    landlord: User = prop.landlord
    landlord_name = landlord.full_name if landlord else "Landlord"

    print(f"\n  Rejecting: {prop.title} ({prop.id})")
    print(f"  Landlord : {landlord_name}")
    print(f"  Reason   : {reason}")

    if dry_run:
        print("  DRY RUN — no changes written.")
        return

    prop.status = PropertyStatus.INACTIVE

    if landlord:
        create_notification(
            db,
            landlord.id,
            "Listing could not be verified",
            f"Your property '{prop.title}' in {prop.neighbourhood}, {prop.city} could not "
            f"be verified at this time. Reason: {reason}. Please update your listing or "
            f"ownership documents and resubmit for review.",
            NotificationType.VERIFICATION,
        )

    print(f"  ✗ Rejected — '{prop.title}' set to INACTIVE. Landlord notified.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify pending G&G Homes property listings.")

    action = parser.add_mutually_exclusive_group()
    action.add_argument("--approve",     metavar="ID", help="Approve a specific property.")
    action.add_argument("--approve-all", action="store_true", help="Approve every pending property.")
    action.add_argument("--reject",      metavar="ID", help="Reject a specific property.")

    parser.add_argument("--reason",  metavar="TEXT", default="Does not meet listing requirements.",
                        help="Rejection reason sent to the landlord (used with --reject).")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to DB.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        # ── approve single ────────────────────────────────────────────────────
        if args.approve:
            prop = db.scalar(
                select(Property)
                .options(joinedload(Property.landlord))
                .where(Property.id == args.approve)
            )
            if not prop:
                print(f"ERROR: No property found with id={args.approve!r}")
                return
            if prop.status != PropertyStatus.PENDING_VERIFICATION:
                print(f"WARNING: Property is '{prop.status.value}', not PENDING_VERIFICATION.")
            approve_property(db, prop, args.dry_run)
            if not args.dry_run:
                db.commit()
            return

        # ── approve all ───────────────────────────────────────────────────────
        if args.approve_all:
            pending = load_pending(db)
            if not pending:
                print("No properties pending verification.")
                return
            print(f"\nApproving {len(pending)} property listing(s)...")
            for prop in pending:
                approve_property(db, prop, args.dry_run)
            if not args.dry_run:
                db.commit()
                print(f"\n  → {len(pending)} listing(s) approved and live. Landlords notified.")
            return

        # ── reject single ─────────────────────────────────────────────────────
        if args.reject:
            prop = db.scalar(
                select(Property)
                .options(joinedload(Property.landlord))
                .where(Property.id == args.reject)
            )
            if not prop:
                print(f"ERROR: No property found with id={args.reject!r}")
                return
            reject_property(db, prop, args.reason, args.dry_run)
            if not args.dry_run:
                db.commit()
            return

        # ── default: list pending ─────────────────────────────────────────────
        pending = load_pending(db)

        print(f"\n{SEPARATOR}")
        print(f"  G&G Homes — Pending Property Verification Report")
        print(f"  Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        print(SEPARATOR)

        if not pending:
            print("\n  No properties awaiting verification.\n")
        else:
            for i, prop in enumerate(pending, start=1):
                print_property(prop, i)

        print(f"\n{SEPARATOR}")
        print(f"  Total pending: {len(pending)} property listing(s)")
        print(f"\n  To approve:     python3 scripts/verify_properties.py --approve <id>")
        print(f"  To approve all: python3 scripts/verify_properties.py --approve-all")
        print(f"  To reject:      python3 scripts/verify_properties.py --reject <id> --reason \"reason\"")
        print(f"{SEPARATOR}\n")

    finally:
        db.close()


if __name__ == "__main__":
    main()
