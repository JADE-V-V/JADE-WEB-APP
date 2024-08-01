"""Contains useful constants and functions for the jadewa package.
"""

from __future__ import annotations
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
    "93c": "D1SUNED (FENDL 3.2b+TENDL2017)",
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


def sorting_func_sphere_sddr(option: str) -> int:
    """sorting function for the pretty names of materials and isotopes"""
    # extract the isotope/material number from the pretty name
    option = option.split("_")[0]
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


def get_info_dfs(
    metadata_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Get the metadata DataFrames to be displayed in the app.

    Parameters
    ----------
    metadata_df : pd.DataFrame
        metadata DataFrame

    Returns
    -------
    sorted_df: pd.DataFrame, df_sddr: pd.DataFrame, df_no_sddr: pd.DataFrame
        the first DF is the complete list of ordered metadata, the second and
        third are the pivot tables showing all the available raw data divided
        by activation and non-activation benchmarks.
    """
    df = metadata_df
    sorted_df = df.set_index(["benchmark_name", "library", "code"])

    sddr_codes = ["d1s"]
    df_sddr = df.set_index("code").loc[sddr_codes].reset_index()
    df_no_sddr = df[~df["code"].isin(sddr_codes)]

    sorted_df = df.set_index(["benchmark_name", "library", "code"])

    for df in [df_sddr, df_no_sddr]:
        df["Available"] = True

    df_sddr = df_sddr.pivot(
        index=["benchmark_name", "code"], columns=["library"], values=["Available"]
    )["Available"]
    df_sddr.fillna(False, inplace=True)

    df_no_sddr = df_no_sddr.pivot(
        index=["benchmark_name", "code"], columns=["library"], values=["Available"]
    )["Available"]
    df_sddr.fillna(False, inplace=True)

    return sorted_df, df_sddr, df_no_sddr


def find_dict_depth(dictionary: dict):
    """Find the depth of a dictionary

    Parameters
    ----------
    dictionary : dict
        dictionary to be assessed

    Returns
    -------
    int
        depth of the dictionary
    """
    if isinstance(dictionary, dict):
        return 1 + (max(map(find_dict_depth, dictionary.values())) if dictionary else 0)

    return 0


def safe_add_ctg_to_dict(dictionary: dict, keys: list[str], value: str) -> dict:
    """Add a category to a dictionary if it does not exist

    Parameters
    ----------
    dictionary : dict
        dictionary to be assessed
    key : str
        key to be added
    value : str
        value to be added

    Returns
    -------
    dict
        dictionary with the added category
    """
    key = keys[0]

    if len(keys) == 1:
        if key in dictionary:
            dictionary[key].append(value)
        else:
            dictionary[key] = [value]
        return

    # if we are not at the last value we need to create another layer and
    # update the dict definition
    if key not in dictionary:
        dictionary[key] = {}

    dictionary = dictionary[key]
    safe_add_ctg_to_dict(dictionary, keys[1:], value)
