"""CLI sub-commands: sign, verify-sign."""

from __future__ import annotations

import sys

from envault.sign import sign_environment, verify_environment, list_signed_environments


def cmd_sign(args) -> None:
    sub = args.sign_cmd

    if sub == "sign":
        result = sign_environment(
            vault_path=args.vault,
            environment=args.environment,
            password=args.password,
            signing_key=args.signing_key,
        )
        status = "updated" if result.updated else "unchanged"
        print(f"[{status}] {result.environment}: {result.signature}")

    elif sub == "verify":
        result = verify_environment(
            vault_path=args.vault,
            environment=args.environment,
            password=args.password,
            signing_key=args.signing_key,
        )
        if result.valid:
            print(f"[OK] Signature for '{result.environment}' is valid.")
        else:
            if result.expected is None:
                print(f"[FAIL] No signature found for '{result.environment}'.", file=sys.stderr)
            else:
                print(f"[FAIL] Signature mismatch for '{result.environment}'.", file=sys.stderr)
                print(f"  stored : {result.expected}", file=sys.stderr)
                print(f"  current: {result.actual}", file=sys.stderr)
            sys.exit(1)

    elif sub == "list":
        envs = list_signed_environments(args.vault)
        if not envs:
            print("No signed environments.")
        else:
            for env in envs:
                print(env)

    else:
        print(f"Unknown sign sub-command: {sub}", file=sys.stderr)
        sys.exit(1)


def register_sign_parser(subparsers) -> None:
    p = subparsers.add_parser("sign", help="Sign and verify environment secret bundles")
    p.add_argument("--vault", required=True, help="Path to vault file")
    sp = p.add_subparsers(dest="sign_cmd", required=True)

    # sign sub-command
    s = sp.add_parser("sign", help="Compute and store HMAC signature for an environment")
    s.add_argument("environment")
    s.add_argument("--password", required=True)
    s.add_argument("--signing-key", required=True, dest="signing_key")

    # verify sub-command
    v = sp.add_parser("verify", help="Verify stored signature against current secrets")
    v.add_argument("environment")
    v.add_argument("--password", required=True)
    v.add_argument("--signing-key", required=True, dest="signing_key")

    # list sub-command
    sp.add_parser("list", help="List environments that have a stored signature")

    p.set_defaults(func=cmd_sign)
