from math import ceil
from uuid import uuid4


def generate_id() -> str:
    return str(uuid4())


def calculate_platform_fee(gross_amount: float) -> float:
    return round(gross_amount * 0.04 * 100) / 100


def pagination_meta(total: int, page: int, page_size: int) -> dict[str, int]:
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": ceil(total / page_size) if page_size else 1,
    }
