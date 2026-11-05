"""Nova Poshta tracking via the official API 2.0."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from aiohttp import ClientError, ClientTimeout

from .base import Carrier, CarrierError, ParcelInfo, ParcelRequest, ParcelStatus

API_URL = "https://api.novaposhta.ua/v2.0/json/"
MAX_DOCUMENTS_PER_REQUEST = 100
TIMEOUT = ClientTimeout(total=20)

# Відповідність кодів статусів Нової пошти нормалізованим статусам.
# УВАГА: коди взято з пам'яті. Звірте їх зі списком статусів у документації API
# та з реальними відповідями перед релізом. Невідомий код потрапляє в UNKNOWN,
# а сирий текст статусу зберігається в атрибутах сенсора.
STATUS_CODES: dict[str, ParcelStatus] = {
    "1": ParcelStatus.NOT_FOUND,
    "2": ParcelStatus.NOT_FOUND,
    "3": ParcelStatus.NOT_FOUND,
    "4": ParcelStatus.CREATED,
    "5": ParcelStatus.IN_TRANSIT,
    "6": ParcelStatus.IN_TRANSIT,
    "101": ParcelStatus.IN_TRANSIT,
    "7": ParcelStatus.READY_FOR_PICKUP,
    "8": ParcelStatus.READY_FOR_PICKUP,
    "9": ParcelStatus.DELIVERED,
    "10": ParcelStatus.DELIVERED,
    "11": ParcelStatus.DELIVERED,
    "102": ParcelStatus.RETURNED,
    "103": ParcelStatus.RETURNED,
    "105": ParcelStatus.RETURNED,
}


def parse_datetime(value: Any) -> datetime | None:
    """Parse Nova Poshta timestamps such as '05.11.2026 13:24:00'."""
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%d.%m.%Y %H:%M:%S")
    except ValueError:
        return None


def parse_documents(items: list[dict[str, Any]], carrier_key: str) -> dict[str, ParcelInfo]:
    """Convert the `data` array of getStatusDocuments into ParcelInfo objects."""
    result: dict[str, ParcelInfo] = {}
    for item in items:
        number = str(item.get("Number", "")).strip()
        if not number:
            continue

        code = str(item.get("StatusCode", ""))
        result[number] = ParcelInfo(
            number=number,
            carrier=carrier_key,
            status=STATUS_CODES.get(code, ParcelStatus.UNKNOWN),
            status_text=str(item.get("Status", "")),
            last_update=parse_datetime(item.get("DateScan")),
            location=item.get("WarehouseRecipient") or item.get("CityRecipient") or None,
        )
    return result


class NovaPoshtaCarrier(Carrier):
    """Client for Nova Poshta API 2.0 (TrackingDocument.getStatusDocuments)."""

    key = "nova_poshta"
    name = "Нова пошта"

    async def track(self, parcels: list[ParcelRequest]) -> dict[str, ParcelInfo]:
        result: dict[str, ParcelInfo] = {}
        for start in range(0, len(parcels), MAX_DOCUMENTS_PER_REQUEST):
            chunk = parcels[start : start + MAX_DOCUMENTS_PER_REQUEST]
            items = await self._request_statuses(chunk)
            result.update(parse_documents(items, self.key))
        return result

    async def _request_statuses(self, chunk: list[ParcelRequest]) -> list[dict[str, Any]]:
        payload = {
            "apiKey": self._api_key or "",
            "modelName": "TrackingDocument",
            "calledMethod": "getStatusDocuments",
            "methodProperties": {
                "Documents": [
                    {"DocumentNumber": parcel.number, "Phone": parcel.phone or ""}
                    for parcel in chunk
                ]
            },
            "language": "UA",
        }

        try:
            async with self._session.post(API_URL, json=payload, timeout=TIMEOUT) as resp:
                resp.raise_for_status()
                body = await resp.json(content_type=None)
        except (ClientError, TimeoutError, ValueError) as err:
            raise CarrierError(f"Запит до Нової пошти не вдався: {err}") from err

        if not isinstance(body, dict):
            raise CarrierError("Нова пошта повернула неочікувану відповідь")

        if not body.get("success"):
            errors = "; ".join(str(e) for e in body.get("errors", [])) or "невідома помилка"
            raise CarrierError(f"Нова пошта повернула помилку: {errors}")

        return body.get("data") or []
