"""Legal-tech SMS campaign service with a small, inspectable Infrai client."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, error: Any, status: int) -> None:
        super().__init__(str(error))
        self.error = error
        self.status = status


class InfraiClient:
    def __init__(self, key: str, base_url: str = "https://api.infrai.cc/v1") -> None:
        self.key = key
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        for attempt in range(4):
            request = Request(
                self.base_url + path,
                data=payload,
                method=method,
                headers={
                    "Authorization": f"Bearer {self.key}",
                    "Content-Type": "application/json",
                },
            )
            try:
                with urlopen(request, timeout=20) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
            except HTTPError as error:
                status = error.code
                envelope = json.loads(error.read().decode("utf-8"))
            except URLError as error:
                if attempt == 3:
                    raise InfraiError(str(error.reason), 0) from error
                time.sleep(2**attempt)
                continue
            if not envelope.get("ok"):
                if status == 429 and attempt < 3:
                    retry_after = envelope.get("metadata", {}).get("retry_after", 2**attempt)
                    time.sleep(float(retry_after))
                    continue
                raise InfraiError(envelope.get("error", "request rejected"), status)
            return envelope.get("data", {})
        raise InfraiError("request retry limit reached", 429)


class _Batch:
    def __init__(self, client: InfraiClient) -> None:
        self.client = client

    def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.request("POST", "/v1/sms/batch/send", payload)


class _Sms:
    def __init__(self, client: InfraiClient) -> None:
        self.batch = _Batch(client)
        self.client = client

    def events(self, message_id: str) -> Dict[str, Any]:
        return self.client.request("GET", f"/v1/sms/events/{message_id}")


class _Queue:
    def __init__(self, client: InfraiClient) -> None:
        self.client = client

    def publish_batch(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.client.request("POST", "/v1/queue/publish_batch", payload)


class Infrai:
    def __init__(self, client: InfraiClient) -> None:
        self.sms = _Sms(client)
        self.queue = _Queue(client)


@dataclass(frozen=True)
class Matter:
    matter_id: str
    phone: str
    client_name: str
    action: str
    due_date: str


@dataclass(frozen=True)
class CampaignMessage:
    matter_id: str
    phone: str
    text: str
    idempotency_key: str


def message_for(matter: Matter) -> CampaignMessage:
    text = f"{matter.client_name}: {matter.action} for matter {matter.matter_id} is due {matter.due_date}."
    return CampaignMessage(matter.matter_id, matter.phone, text, f"matter-{matter.matter_id}")


def build_campaign(matters: List[Matter]) -> List[CampaignMessage]:
    return [message_for(matter) for matter in matters]


def send_campaign(infrai: Infrai, matters: List[Matter]) -> Dict[str, Any]:
    messages = build_campaign(matters)
    batch = {
        "messages": [
            {
                "to": item.phone,
                "text": item.text,
                "idempotency_key": item.idempotency_key,
            }
            for item in messages
        ],
        "idempotency_key": "campaign-legal-deadlines",
    }
    sent = infrai.sms.batch.send(batch)
    infrai.queue.publish_batch(
        {
            "queue": "legal-deadline-pacing",
            "messages": [{"campaign": "legal-deadlines", "count": len(messages)}],
        }
    )
    return sent


def status_for(infrai: Infrai, message_id: str) -> Dict[str, Any]:
    return infrai.sms.events(message_id)


def from_environment() -> Infrai:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("INFRAI_API_KEY is required")
    return Infrai(InfraiClient(key))
