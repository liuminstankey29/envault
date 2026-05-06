"""Command-line interface for envault."""

import sys
import getpass
import argparse

from envault.vault import write_secrets, read_secrets, list_environments


def cmd_set(args):
    """Set one or more secrets in a given environment."""
    password = getpass.getpass("Vault password: ")
    pairs = {}
    for item in args.pairs:
        if "=" not in item:
            print(f"Error: expected KEY=VALUE, got {item!r}", file=sys.stderr)
            sys.exit(1)
        key, _, value = item.partition("=")
        pairs[key.strip()] = value.strip()
    write_secrets(args.vault, args.env, pairs, password)
    print(f"Wrote {len(pairs)} secret(s) to environment '{args.env}'.")


def cmd_get(args):
    """Print secrets for a given environment."""
    password = getpass.getpass("Vault password: ")
    secrets = read_secrets(args.vault, args.env, password)
    if args.key:
        if args.key not in secrets:
            print(f"Error: key '{args.key}' not found in environment '{args.env}'.", file=sys.stderr)
            sys.exit(1)
        print(secrets[args.key])
    else:
        for k, v in sorted(secrets.items()):
            print(f"{k}={v}")


def cmd_list(args):
    """List all environments stored in the vault."""
    envs = list_environments(args.vault)
    if not envs:
        print("No environments found.")
    else:
        for env in sorted(envs):
            print(env)


def build_parser():
    parser = argparse.ArgumentParser(
        prog="envault",
        description="Encrypted .env file manager with per-environment secret rotation.",
    )
    parser.add_argument("--vault", default="secrets.vault.json", help="Path to vault file (default: secrets.vault.json)")

    sub = parser.add_subparsers(dest="command", required=True)

    p_set = sub.add_parser("set", help="Set secrets in an environment")
    p_set.add_argument("env", help="Environment name (e.g. production)")
    p_set.add_argument("pairs", nargs="+", metavar="KEY=VALUE", help="Secret key-value pairs")
    p_set.set_defaults(func=cmd_set)

    p_get = sub.add_parser("get", help="Get secrets from an environment")
    p_get.add_argument("env", help="Environment name")
    p_get.add_argument("key", nargs="?", default=None, help="Specific key to retrieve (omit to print all)")
    p_get.set_defaults(func=cmd_get)

    p_list = sub.add_parser("list", help="List all environments")
    p_list.set_defaults(func=cmd_list)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
