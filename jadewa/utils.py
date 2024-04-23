"""Contains useful constants and functions for the jadewa package.
"""

import re
from f4enix.input.libmanager import LibManager

LIB_NAMES = {
    "21c": "FENDL 2.1c",
    "30c": "FENDL 3.0",
    "31c": "FENDL 3.1d",
    "32c": "FENDL 3.2b",
    "70c": "ENDFB VII.0",
    "00c": "ENDFB VIII.0",
    "34y": "IRDFF II",
    "03c": "JEFF 3.3",
}
LIB_SUFFIXES = {v: k for k, v in LIB_NAMES.items()}

MATERIAL_NUMBERS = {
    "SS316L(N)-IG": "M101",
    "Water": "M400",
    "Boron Carbide": "M203",
    "Ordinary Concrete": "M200",
    "Natural Silicon": "M900",
    "Polyethylene (non-borated)": "M901",
    "Tungsten": "M74",
    "CaF2": "M10",
}
MATERIAL_NAMES = {v: k for k, v in MATERIAL_NUMBERS.items()}

# patterns
MAT_ISO_PATTERN = re.compile(r"[mM]*\d+")

LIB_MANAGER = LibManager()


def sorting_func(option: str):
    """function to sort correctly the materials and isotopes options"""
    # extract the isotope/material number from the pretty name
    try:
        num = int(MAT_ISO_PATTERN.search(option).group())
    except ValueError:
        # it is a material, return 0 so it is placed first
        num = 0
    return num


def get_pretty_mat_iso_names(raw_names: list[str]):
    # the names should be ordered material first and then all isotopes using
    # as order the zaid integer number. Sorting is easier in the raw list
    raw_names.sort(key=sorting_func)

    pretty_names = []
    for name in raw_names:
        # only the material/isotope needs to be assessed
        name = MAT_ISO_PATTERN.search(name).group()

        try:
            pretty_names.append(MATERIAL_NAMES[name])
        except KeyError:
            pretty_names.append(LIB_MANAGER.get_zaidname(name)[1])

    return pretty_names


def get_mat_iso_code(name: str, code="mcnp"):
    try:
        return code + MATERIAL_NUMBERS[name]
    except KeyError:
        return code + LIB_MANAGER.get_zaidnum(name)
