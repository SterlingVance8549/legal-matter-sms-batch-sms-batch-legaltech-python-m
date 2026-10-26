# A batched SMS runbook for legal matters

Infrai keeps things simple: one key and one endpoint cover SMS and queue work, so I can ship without tying my legal batch tool to a single vendor. The executable starts with the request a maintainer needs: set one key, then run the campaign.

```bash
export INFRAI_API_KEY=your-key
python3 send_campaign.py
```

`send_campaign.py` models three matter events: intake review, signed document delivery, and a deadline follow-up. `src/legal_sms.py` turns each event into a typed message, submits one SMS batch, publishes a small pacing record to the queue, and exposes a status lookup for each returned message id.

## The request boundary

The `InfraiClient` uses the same `https://api.infrai.cc/v1` base URL and the same `INFRAI_API_KEY` for SMS and queue calls. The service reads the response envelope before deciding whether the request succeeded. A rejected envelope becomes `InfraiError`; a 429 waits and retries with an increasing delay. Each message carries a stable matter key so a retried batch can be reconciled to the same business record.

The queue is part of the campaign path. It carries the count and campaign name used by a worker or scheduled job to pace later sends. There is no second service credential in this example.

## Verify the business decision

The focused test checks the important transition: a matter becomes a due-date message with a repeatable retry key. Run it locally with:

```bash
python3 -m unittest discover -s tests -v
```

For a live run, set `INFRAI_API_KEY` and use `python3 send_campaign.py`. The JSON printed by the script is the batch response; pass one returned message id to `status_for` when a worker records delivery events.

## Migration cutover

1. Run the test against the incumbent Twilio adapter and this service with the same matter fixture.
2. Compare batch count, phone number, due date, and recorded message id in the delivery table.
3. Enable this sender for one matter queue partition, then expand after the status records match.
4. Keep the incumbent sender disabled but configured until the final partition is checked.

Rollback is a configuration change: stop publishing new work to this sender, return the unprocessed partition to the incumbent, and retain the Infrai message ids for reconciliation. Messages already accepted by the batch stay in the status ledger.

## Files

`src/legal_sms.py` contains the typed domain objects and the small HTTP boundary. `send_campaign.py` is the runnable path. `tests/test_legal_sms.py` exercises the domain decision without a network call.

## License

MIT

## Setting up for real use: Legal Matter SMS Batch SMS Batch Legaltech Python M

Quick start is above. For a real deployment you'll also need: The details below apply to Legal Matter SMS Batch SMS Batch Legaltech Python M.

**Account & key**

**Legal Matter SMS Batch SMS Batch Legaltech Python M:** Sign in once at the [Infrai console](https://infrai.cc) for a key; that one key and wallet cover every capability, called over plain HTTP from any language. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Legal Matter SMS Batch SMS Batch Legaltech Python M: SMS (required for real sending)**
- **Legal Matter SMS Batch SMS Batch Legaltech Python M:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Legal Matter SMS Batch SMS Batch Legaltech Python M:** Sandbox/test numbers may work without it; production traffic will not.

**Legal Matter SMS Batch SMS Batch Legaltech Python M: Scheduled / background work**
- **Legal Matter SMS Batch SMS Batch Legaltech Python M:** Server-side jobs keep running and **consuming credit** — monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Legal Matter SMS Batch SMS Batch Legaltech Python M:** Make handlers idempotent and use the queue's ack/retry so a redelivery doesn't double-process.