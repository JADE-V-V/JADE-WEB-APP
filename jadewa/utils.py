"""Contains useful constants and functions for the jadewa package.
"""

import re
from f4enix.input.libmanager import LibManager
import pandas as pd


LIB_NAMES = {
    "21c": "FENDL 2.1c",
    "30c": "FENDL 3.0",
    "31c": "FENDL 3.1d",
    "32c": "FENDL 3.2b",
    "70c": "ENDFB VII.0",
    "00c": "ENDFB VIII.0",
    "34y": "IRDFF II",
    "03c": "JEFF 3.3",
    "99c": "D1SUNED (FENDL 3.1d+EAF2007)",
    "exp": "experiment",
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


def sorting_func(option: str) -> int:
    """sorting function for the pretty names of materials and isotopes"""
    # extract the isotope/material number from the pretty name
    try:
        num = int(MAT_ISO_PATTERN.search(option).group())
    except ValueError:
        # it is a material, return 0 so it is placed first
        num = 0
    return num


def get_pretty_mat_iso_names(raw_names: list[str]) -> list[str]:
    """Get the pretty names of a list of materials/isotopes raw names

    Parameters
    ----------
    raw_names : list[str]
        raw names of the materials (e.g. mcnpM900) and isotopes (e.g. mcnp1001)

    Returns
    -------
    list[str]
        pretty names of the materials/isotopes
    """
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


def get_pretty_lib_names(raw_names: list[str]) -> list[str]:
    """Get the pretty names of a list of libraries suffixes

    Parameters
    ----------
    raw_names : list[str]
        libary suffixes (e.g. 21c, 30c, 31c)

    Returns
    -------
    list[str]
        pretty names of the libraries (e.g. FENDL 2.1c, FENDL 3.0, FENDL 3.1d)
    """
    libs = []
    for lib in raw_names:
        libs.append(LIB_NAMES[lib])
    return libs


def get_mat_iso_code(name: str) -> str:
    """Get the code of a material/isotope from its pretty name

    Parameters
    ----------
    name : str
        pretty name of the material/isotope (e.g. Natural Silicon, H-1, Ne-1)

    Returns
    -------
    str
        code of the material/isotope (e.g. mcnpM900, mcnp1001, mcnp10001)
    """
    try:
        return MATERIAL_NUMBERS[name]
    except KeyError:
        return LIB_MANAGER.get_zaidnum(name)


def get_lib_suffix(name: str) -> str:
    """Get the suffix of a library from its pretty name

    Parameters
    ----------
    name : str
        pretty name of the library (e.g. FENDL 2.1c, FENDL 3.0, FENDL 3.1d)

    Returns
    -------
    str
        suffix of the library (e.g. 21c, 30c, 31c)
    """
    return LIB_SUFFIXES[name]


def string_ints_converter(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Take the selected column of a Dataframe, connvert all elements to int
    if possible and then reconvert to string. This allows '1.0' and '1' to be
    the same index. If no element was a string in the first place, do not change
    anything.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame to be converted
    column : str
        columns to be converted

    Returns
    -------
    pd.DataFrame
        DataFrame with the selected columns converted to string
    """
    try:
        df[column].astype(float)
        return df
    except ValueError:
        values = df[column].values
        new_values = []
        for value in values:
            try:
                new_values.append(str(int(float(value))))
            except ValueError:
                new_values.append(value)
        df[column] = new_values
        return df
