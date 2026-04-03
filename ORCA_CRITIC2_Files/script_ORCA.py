#!/usr/bin/env python3

# =============================================================================
# This script was NOT USED as Fran provided me access to an exisiting set of scripts.
# =============================================================================






# -----------------------------------------------------------------------------
# Function: generate_orca_sp_folders.py
# Purpose :
#   Scan a directory of .xyz files, create one job folder per molecule, and
#   generate separate ORCA single-point input/output locations for:
#       - N     (neutral)
#       - N+1   (anion)
#       - N-1   (cation)
#
#   For each input XYZ:
#       molecule.xyz
#
#   The script creates:
#       molecule/
#         ├── source/
#         │    └── molecule.xyz
#         ├── N/
#         │    └── molecule_N.inp
#         ├── N_plus/
#         │    └── molecule_Nplus.inp
#         └── N_minus/
#              └── molecule_Nminus.inp
#
# Purpose :
#   This is meant to automate the setup stage before running ORCA for hardness:
#
#       η = [ E(N-1) + E(N+1) - 2E(N) ] / 2
#
# Inputs  :
#   --xyz-dir       Directory containing input .xyz files
#   --out-dir       Directory where molecule folders will be created
#   --method        ORCA method line, default: "B3LYP 6-31+G** SP"
#   --mult-neutral  Neutral multiplicity, default: 1
#   --mult-charged  Charged-state multiplicity, default: 2
#   --copy-xyz      If set, copies xyz into each charge-state folder as well
#   --overwrite     If set, overwrites existing .inp files
#
# Output  :
#   Folder tree and ORCA input files for N / N+1 / N-1 jobs
#
# Notes   :
#   - Assumes standard XYZ format:
#         line 1 -> atom count
#         line 2 -> comment
#         line 3+ -> coordinates
#   - Neutral is assumed to be closed-shell singlet unless changed
#   - N+1 and N-1 are assumed to be doublets unless changed
#   - This script PREPARES jobs only; it does not run ORCA
# -----------------------------------------------------------------------------


from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import List


# -----------------------------------------------------------------------------
# Function: read_xyz_coordinates
# Purpose :
#   Read an XYZ file and return only the coordinate block expected by ORCA.
#
# Inputs  :
#   xyz_path : Path
#       Path to the XYZ file
#
# Output  :
#   List[str]
#       Coordinate lines only (no atom count / no comment line)
#
# Notes   :
#   Raises a ValueError if the XYZ file is too short to be valid.
# -----------------------------------------------------------------------------
def read_xyz_coordinates(xyz_path: Path) -> List[str]:
    lines = xyz_path.read_text(encoding="utf-8").splitlines()

    if len(lines) < 3:
        raise ValueError(f"Invalid XYZ file (too short): {xyz_path}")

    coords = [line.rstrip() for line in lines[2:] if line.strip()]
    if not coords:
        raise ValueError(f"No coordinate lines found in: {xyz_path}")

    return coords


# -----------------------------------------------------------------------------
# Function: build_orca_input
# Purpose :
#   Construct the ORCA input text for a single-point job at a fixed geometry.
#
# Inputs  :
#   method_line  : str
#       ORCA keyword line, e.g. "B3LYP 6-31+G** SP"
#   charge       : int
#       Molecular charge
#   multiplicity : int
#       Spin multiplicity
#   coords       : List[str]
#       Coordinate block from XYZ
#
# Output  :
#   str
#       Complete ORCA input file text
# -----------------------------------------------------------------------------
def build_orca_input(
    method_line: str,
    charge: int,
    multiplicity: int,
    coords: List[str],
) -> str:
    body = "\n".join(coords)
    return f"""! {method_line}

* xyz {charge} {multiplicity}
{body}
*
"""


# -----------------------------------------------------------------------------
# Function: safe_write_text
# Purpose :
#   Write a text file, respecting overwrite preference.
#
# Inputs  :
#   path      : Path
#       Target file path
#   text      : str
#       Content to write
#   overwrite : bool
#       Whether existing files may be overwritten
#
# Output  :
#   None
#
# Notes   :
#   Raises FileExistsError if overwrite=False and file already exists.
# -----------------------------------------------------------------------------
def safe_write_text(path: Path, text: str, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    path.write_text(text, encoding="utf-8")


# -----------------------------------------------------------------------------
# Function: prepare_single_molecule
# Purpose :
#   Create the folder structure and ORCA inputs for one XYZ file.
#
# Inputs  :
#   xyz_path        : Path
#       Path to source XYZ file
#   out_root        : Path
#       Root output directory
#   method_line     : str
#       ORCA method line
#   mult_neutral    : int
#       Multiplicity for neutral state
#   mult_charged    : int
#       Multiplicity for charged states
#   copy_xyz        : bool
#       Whether to copy XYZ into each state folder
#   overwrite       : bool
#       Whether to overwrite existing files
#
# Output  :
#   None
# -----------------------------------------------------------------------------
def prepare_single_molecule(
    xyz_path: Path,
    out_root: Path,
    method_line: str,
    mult_neutral: int,
    mult_charged: int,
    copy_xyz: bool,
    overwrite: bool,
) -> None:
    molecule_name = xyz_path.stem
    mol_root = out_root / molecule_name

    source_dir = mol_root / "source"
    n_dir = mol_root / "N"
    n_plus_dir = mol_root / "N_plus"
    n_minus_dir = mol_root / "N_minus"

    for directory in (source_dir, n_dir, n_plus_dir, n_minus_dir):
        directory.mkdir(parents=True, exist_ok=True)

    coords = read_xyz_coordinates(xyz_path)

    # -------------------------------------------------------------------------
    # Copy original XYZ into source folder for provenance / traceability
    # -------------------------------------------------------------------------
    source_xyz = source_dir / xyz_path.name
    if not source_xyz.exists() or overwrite:
        shutil.copy2(xyz_path, source_xyz)

    # Optional duplication into each job folder
    if copy_xyz:
        for target_dir in (n_dir, n_plus_dir, n_minus_dir):
            target_xyz = target_dir / xyz_path.name
            if not target_xyz.exists() or overwrite:
                shutil.copy2(xyz_path, target_xyz)

    # -------------------------------------------------------------------------
    # Build ORCA input files
    # -------------------------------------------------------------------------
    n_inp = build_orca_input(
        method_line=method_line,
        charge=0,
        multiplicity=mult_neutral,
        coords=coords,
    )
    n_plus_inp = build_orca_input(
        method_line=method_line,
        charge=-1,
        multiplicity=mult_charged,
        coords=coords,
    )
    n_minus_inp = build_orca_input(
        method_line=method_line,
        charge=+1,
        multiplicity=mult_charged,
        coords=coords,
    )

    safe_write_text(
        n_dir / f"{molecule_name}_N.inp",
        n_inp,
        overwrite=overwrite,
    )
    safe_write_text(
        n_plus_dir / f"{molecule_name}_Nplus.inp",
        n_plus_inp,
        overwrite=overwrite,
    )
    safe_write_text(
        n_minus_dir / f"{molecule_name}_Nminus.inp",
        n_minus_inp,
        overwrite=overwrite,
    )


# -----------------------------------------------------------------------------
# Function: parse_args
# Purpose :
#   Parse command-line arguments.
#
# Inputs  :
#   None
#
# Output  :
#   argparse.Namespace
# -----------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate per-molecule ORCA SP folders for N, N+1, and N-1 "
            "from a directory of XYZ files."
        )
    )
    parser.add_argument(
        "--xyz-dir",
        required=True,
        type=Path,
        help="Directory containing input .xyz files",
    )
    parser.add_argument(
        "--out-dir",
        required=True,
        type=Path,
        help="Directory where molecule job folders will be created",
    )
    parser.add_argument(
        "--method",
        default="B3LYP 6-31+G** SP",
        help='ORCA method line without leading "!"',
    )
    parser.add_argument(
        "--mult-neutral",
        type=int,
        default=1,
        help="Multiplicity for neutral state (default: 1)",
    )
    parser.add_argument(
        "--mult-charged",
        type=int,
        default=2,
        help="Multiplicity for N+1 and N-1 states (default: 2)",
    )
    parser.add_argument(
        "--copy-xyz",
        action="store_true",
        help="Also copy the source XYZ into each of N / N_plus / N_minus",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing .inp files if present",
    )
    return parser.parse_args()


# -----------------------------------------------------------------------------
# Function: main
# Purpose :
#   Drive the batch setup for all XYZ files in the input directory.
#
# Inputs  :
#   None
#
# Output  :
#   None
#
# Notes   :
#   Prints a short status line per processed molecule.
# -----------------------------------------------------------------------------
def main() -> None:
    args = parse_args()

    xyz_dir: Path = args.xyz_dir.expanduser().resolve()
    out_dir: Path = args.out_dir.expanduser().resolve()

    if not xyz_dir.exists():
        raise FileNotFoundError(f"XYZ directory does not exist: {xyz_dir}")
    if not xyz_dir.is_dir():
        raise NotADirectoryError(f"XYZ path is not a directory: {xyz_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)

    xyz_files = sorted(xyz_dir.glob("*.xyz"))
    if not xyz_files:
        raise FileNotFoundError(f"No .xyz files found in: {xyz_dir}")

    print(f"Found {len(xyz_files)} XYZ file(s) in: {xyz_dir}")
    print(f"Output root: {out_dir}\n")

    for xyz_path in xyz_files:
        prepare_single_molecule(
            xyz_path=xyz_path,
            out_root=out_dir,
            method_line=args.method,
            mult_neutral=args.mult_neutral,
            mult_charged=args.mult_charged,
            copy_xyz=args.copy_xyz,
            overwrite=args.overwrite,
        )
        print(f"[OK] Prepared jobs for: {xyz_path.stem}")

    print("\nDone.")


if __name__ == "__main__":
    main()