"""Contains useful constants and functions for the jadewa package.
"""

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

MATERIAL_NAMES = {
    "SS316L(N)-IG": "M101",
    "Water": "M400",
    "Boron Carbide": "M203",
    "Ordinary Concrete": "M200",
    "Natural Silicon": "M900",
    "Polyethylene (non-borated)": "M901",
    "Tungsten": "M74",
    "CaF2": "M10",
}
MATERIAL_NUMBERS = {v: k for k, v in MATERIAL_NAMES.items()}
