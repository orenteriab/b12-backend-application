import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

SUBMIT_URL = "https://b12.io/apply/submission"


def build_payload():
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"
    return {
        "action_run_link": os.environ["ACTION_RUN_LINK"],
        "email": os.environ["EMAIL"],
        "name": os.environ["NAME"],
        "repository_link": os.environ["REPOSITORY_LINK"],
        "resume_link": os.environ["RESUME_LINK"],
        "timestamp": timestamp,
    }


def canonicalize(payload):
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def sign(body, secret):
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def main():
    signing_secret = os.environ["SIGNING_SECRET"]

    payload = build_payload()
    body = canonicalize(payload)

    signature = sign(body, signing_secret)

    print(f"Submitting application for {payload['name']}...")
    print(f"Payload: {body.decode('utf-8')}")

    req = Request(
        SUBMIT_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Signature-256": signature,
        },
        method="POST",
    )

    try:
        with urlopen(req) as response:
            response_body = response.read().decode("utf-8")
            data = json.loads(response_body)
            print(f"Response status: {response.status}")
            print(f"Response body: {response_body}")
            if data.get("success"):
                print(f"\nReceipt: {data['receipt']}")
            else:
                print("Submission was not successful.")
                sys.exit(1)
    except HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        sys.exit(1)
    except URLError as e:
        print(f"URL Error: {e.reason}")
        sys.exit(1)


if __name__ == "__main__":
    main()
