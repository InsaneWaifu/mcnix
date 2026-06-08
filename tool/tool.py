#!/usr/bin/env python3
import json
import os
import shutil
from pathlib import Path


def load_schema(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)

def sync_plugins(current_schema_path: str,
                 new_schema_path: str,
                 plugins_dir: str):
    current_schema_path = Path(current_schema_path)
    new_schema_path = Path(new_schema_path)
    plugins_dir = Path(plugins_dir)

    plugins_dir.mkdir(parents=True, exist_ok=True)

    current = load_schema(current_schema_path)
    new = load_schema(new_schema_path)

    current_plugins = {p["jarName"]: p for p in current.get("plugins", [])}
    new_plugins = {p["jarName"]: p for p in new.get("plugins", [])}

    for jar_name in current_plugins:
        if jar_name not in new_plugins:
            deployed_file = plugins_dir / f"{jar_name}.jar"
            if deployed_file.exists() or deployed_file.is_symlink():
                print(f"Removing: {deployed_file}")
                deployed_file.unlink()

    for jar_name, plugin in new_plugins.items():
        src = Path(plugin["jar"])
        dst = plugins_dir / f"{jar_name}.jar"

        if not src.exists():
            raise FileNotFoundError(f"Plugin jar not found: {src}")

        if dst.exists() or dst.is_symlink():
            dst.unlink()

        print(f"Linking: {src} -> {dst}")
        dst.symlink_to(src)

    print(f"Updating schema symlink: {current_schema_path} -> {new_schema_path}")

    if current_schema_path.exists() or current_schema_path.is_symlink():
        current_schema_path.unlink()

    current_schema_path.symlink_to(new_schema_path)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--current-schema", required=True)
    parser.add_argument("--new-schema", required=True)
    parser.add_argument("--plugins-dir", required=True)

    args = parser.parse_args()

    sync_plugins(
        args.current_schema,
        args.new_schema,
        args.plugins_dir
    )
