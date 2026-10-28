"""Stable record envelope for data returned by external connectors."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class DataRecord:
    """A source-neutral record that retains original source attributes."""

    id: str | None
    source: str
    retrieved_at: str
    attributes: dict[str, Any]
    geometry: dict[str, Any] | None = None
    source_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_record(
    value: Any,
    *,
    source: str,
    source_url: str | None = None,
    retrieved_at: str | None = None,
) -> DataRecord:
    """Wrap a JSON object or GeoJSON Feature in the common record envelope."""
    if not isinstance(value, dict):
        raise ValueError("Each source record must be a JSON object.")

    properties = value.get("properties") if value.get("type") == "Feature" else None
    attributes = properties if isinstance(properties, dict) else value
    identifier = value.get("id", attributes.get("id"))
    geometry = value.get("geometry") if value.get("type") == "Feature" else None
    timestamp = retrieved_at or datetime.now(timezone.utc).isoformat()

    return DataRecord(
        id=str(identifier) if identifier is not None else None,
        source=source,
        retrieved_at=timestamp,
        attributes=attributes,
        geometry=geometry if isinstance(geometry, dict) else None,
        source_url=source_url,
    )


def normalize_payload(
    payload: Any,
    *,
    source: str,
    source_url: str | None = None,
) -> list[DataRecord]:
    """Normalize common JSON, GeoJSON, and paginated API response shapes."""
    if isinstance(payload, list):
        values = payload
    elif isinstance(payload, dict) and payload.get("type") == "FeatureCollection":
        values = payload.get("features")
    elif isinstance(payload, dict) and isinstance(payload.get("results"), list):
        values = payload["results"]
    elif isinstance(payload, dict) and isinstance(payload.get("data"), list):
        values = payload["data"]
    else:
        values = [payload]

    if not isinstance(values, list):
        raise ValueError("The source response does not contain a record list.")
    retrieved_at = datetime.now(timezone.utc).isoformat()
    return [
        normalize_record(
            item,
            source=source,
            source_url=source_url,
            retrieved_at=retrieved_at,
        )
        for item in values
    ]
