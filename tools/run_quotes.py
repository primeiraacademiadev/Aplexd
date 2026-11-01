#!/usr/bin/env python3
"""Interactive local launcher for Aplexd Yahoo quote exports (no account credentials)."""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main():
    p = argparse.ArgumentParser(description="Select an Aplexd CSV and generate <name>.out.csv")
    p.add_argument("--directory", type=Path, default=ROOT / ".quotes", help="Directory with source CSVs")
    p.add_argument("--delay", type=float, default=2.5)
    p.add_argument("--max-requests", type=int, default=100)
    p.add_argument("--cache-hours", type=float, default=6)
    p.add_argument("--ticker", action="append", default=[], help="Mapping SYMBOL=YAHOO, repeatable")
    args = p.parse_args()
    folder = args.directory.expanduser().resolve()
    if not folder.is_dir():
        print(f"Diretoria de cotações inexistente: {folder}", file=sys.stderr)
        return 2
    sources = sorted(
        (f for f in folder.glob("*.csv") if f.is_file() and not f.name.lower().endswith(".out.csv")),
        key=lambda f: (f.with_name(f.stem + ".out.csv").exists(), f.name.casefold())
    )
    if not sources:
        print(f"Não há ficheiros CSV de entrada em {folder}.")
        return 1
    print("\nAplexd — atualização de cotações")
    for i, f in enumerate(sources, 1):
        output = f.with_name(f.stem + ".out.csv")
        state = "JÁ PROCESSADO" if output.exists() else "POR PROCESSAR"
        print(f"  {i:2}. [{state}] {f.name}  ->  {output.name}")
    default = next((i for i, f in enumerate(sources, 1) if not f.with_name(f.stem + ".out.csv").exists()), 1)
    try:
        choice = input(f"\nEscolhe o número [Enter={default}, q=sair]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelado.")
        return 1
    if choice in {"q", "quit", "s", "sair"}:
        return 0
    try:
        selected = default if not choice else int(choice)
        if not (1 <= selected <= len(sources)):
            raise ValueError
    except ValueError:
        print("Seleção inválida.", file=sys.stderr)
        return 2
    source = sources[selected - 1]
    output = source.with_name(source.stem + ".out.csv")
    if output.exists():
        try:
            answer = input(f"{output.name} já existe. Substituir? [s/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return 1
        if answer not in {"s", "sim", "y", "yes"}:
            print("Mantido sem alterações.")
            return 0
    command = [sys.executable, str(ROOT / "tools" / "aplexd_yfinance.py"), str(source),
               "-o", str(output), "--delay", str(args.delay),
               "--max-requests", str(args.max_requests),
               "--cache-hours", str(args.cache_hours)]
    for item in args.ticker:
        command.extend(["--ticker", item])
    print(f"\nA processar {source.name} -> {output.name}\n")
    return subprocess.call(command, cwd=str(ROOT))

if __name__ == "__main__":
    raise SystemExit(main())
