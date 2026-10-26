import json

from src.legal_sms import Matter, from_environment, send_campaign


def main() -> None:
    matters = [
        Matter("MAT-104", "+15550101", "Jordan Lee", "signed document delivery", "2026-11-03"),
        Matter("MAT-219", "+15550102", "Casey Chen", "matter intake review", "2026-11-07"),
        Matter("MAT-311", "+15550103", "Morgan Diaz", "deadline follow-up", "2026-11-12"),
    ]
    print(json.dumps(send_campaign(from_environment(), matters), indent=2))


if __name__ == "__main__":
    main()
