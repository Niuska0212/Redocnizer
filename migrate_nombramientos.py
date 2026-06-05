#!/usr/bin/env python3
"""
Migra contenido de carpetas NOMBRAMIENTOS a 06 NOMBRAMIENTOS.

Este script es independiente del programa principal y solo necesita que el usuario
indique la carpeta raíz donde está la estructura de expedientes.

Ejemplo:
    "Z:\\Proyecto-modular-1\\Contratos"
"""

import argparse
import os
import shutil
import sys


def normalize_path(value: str) -> str:
    if not value:
        return value
    return os.path.normpath(value.strip())


def find_nombramientos_dirs(root_dir: str):
    for current_dir, dirnames, _ in os.walk(root_dir):
        if os.path.basename(current_dir).strip().upper() == "NOMBRAMIENTOS":
            yield current_dir


def move_contents(old_dir: str, new_dir: str):
    moved = 0
    overwritten = 0

    os.makedirs(new_dir, exist_ok=True)

    for root, _, files in os.walk(old_dir):
        rel_path = os.path.relpath(root, old_dir)
        destination_root = new_dir if rel_path == "." else os.path.join(new_dir, rel_path)
        os.makedirs(destination_root, exist_ok=True)

        for filename in files:
            source_path = os.path.join(root, filename)
            destination_path = os.path.join(destination_root, filename)

            if os.path.exists(destination_path):
                os.remove(destination_path)
                overwritten += 1

            shutil.move(source_path, destination_path)
            moved += 1

    return moved, overwritten


def cleanup_empty_dirs(start_dir: str):
    removed = 0
    for root, dirs, files in os.walk(start_dir, topdown=False):
        if not dirs and not files:
            try:
                os.rmdir(root)
                removed += 1
            except OSError:
                pass
    return removed


def migrate_root(root_dir: str, limit_to_professor: str = None):
    if not os.path.isdir(root_dir):
        raise FileNotFoundError(f"No se encontró la carpeta raíz: {root_dir}")

    search_root = root_dir
    if limit_to_professor:
        search_root = os.path.join(root_dir, normalize_path(limit_to_professor))
        if not os.path.isdir(search_root):
            raise FileNotFoundError(f"No se encontró la carpeta de profesor: {search_root}")

    summary = []

    for old_dir in find_nombramientos_dirs(search_root):
        parent_path = os.path.dirname(old_dir)
        new_dir = os.path.join(parent_path, "06 NOMBRAMIENTOS")

        moved, overwritten = move_contents(old_dir, new_dir)
        removed_dirs = cleanup_empty_dirs(old_dir)

        summary.append({
            "old_dir": old_dir,
            "new_dir": new_dir,
            "moved": moved,
            "overwritten": overwritten,
            "removed_empty_dirs": removed_dirs,
        })

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Migra NOMBRAMIENTOS a 06 NOMBRAMIENTOS dentro de la estructura de expedientes."
    )
    parser.add_argument("--root", help="Carpeta raíz seleccionada por el usuario")
    parser.add_argument(
        "--professor-folder",
        help="Ruta relativa al profesor dentro de la raíz para limitar la migración.",
    )
    args = parser.parse_args()

    root_dir = normalize_path(args.root or input("Ruta raíz del expediente: ").strip())
    if not root_dir:
        print("Error: se requiere la ruta raíz.")
        sys.exit(1)

    try:
        summary = migrate_root(root_dir, limit_to_professor=args.professor_folder)
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(2)

    if not summary:
        print("No se encontró ninguna carpeta NOMBRAMIENTOS para migrar.")
        return

    print("Migración completada:")
    for item in summary:
        print(f"- {item['old_dir']} -> {item['new_dir']}")
        print(f"  Archivos movidos: {item['moved']}, sobrescritos: {item['overwritten']}, carpetas vacías removidas: {item['removed_empty_dirs']}")


if __name__ == "__main__":
    main()
