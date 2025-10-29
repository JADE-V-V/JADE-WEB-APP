"""Main streamlit app entry point."""

from __future__ import annotations

from cProfile import label

import pandas as pd
import streamlit as st

from jadewa.plotter import select_visible_libs
from jadewa.processor import Processor
from jadewa.status import Status
from jadewa.utils import (
    LIB_NAMES,
    PROTECTED_STRINGS,
    find_dict_depth,
    get_info_dfs,
    safe_add_ctg_to_dict,
)

# Get list of CSV files in current directory
OWNER = "JADE-V-V"
REPO = "JADE-RAW-RESULTS"
BRANCH = "jade_v4_raw_results"


# Initialize status and processor
@st.cache_data
def get_status_processor() -> tuple[Status, Processor]:
    """Get the status and processor objects"""
    session_status = Status.from_github(OWNER, REPO, branch=BRANCH)
    session_processor = Processor(session_status)
    return session_status, session_processor


def select_benchmark(available_benchmarks: list[str]) -> str:
    """Create a selectbox for the benchmark selection and return the selected benchmark.

    Parameters
    ----------
    available_benchmarks : list[str]
        list of available benchmarks

    Returns
    -------
    str
        selected benchmark
    """
    # Sort the available benchmarks alphabetically
    available_benchmarks = sorted(available_benchmarks)
    flag_split, ctg_dict = _split_options(available_benchmarks, divisions=None)

    if flag_split:
        selected_benchmark = _get_split_selection(ctg_dict, "benchmark")
    else:
        selected_benchmark = st.selectbox(
            "Select benchmark", available_benchmarks, index=None, key="benchmark"
        )

    return selected_benchmark


def select_ref_lib(selected_benchmark: str, status: Status) -> str:
    """Create a selectbox for the reference library selection and return the selected library.
    In case of an experimental benchmark, the reference library is set to "exp" by default,
    but the user can change it.

    Parameters
    ----------
    selected_benchmark : str
        selected benchmark
    status : Status
        status object describing the available data from JADE runs

    Returns
    -------
    str
        selected reference library
    """
    lib_options = status.get_libraries(selected_benchmark)
    # if experimental data is available, set is as the reference
    # but allow the user to change it
    if "exp" in lib_options:
        index = lib_options.index("exp")
        lib_options[index] = "Experiment"
    else:
        index = None
    ref_lib = st.selectbox(
        "Select reference library", lib_options, index=index, key="lib"
    )
    if ref_lib == "Experiment":
        ref_lib = "exp"
    return ref_lib


def select_ref_code(selected_benchmark: str, ref_lib: str, status: Status) -> str:
    """Create a selectbox for the reference code selection and return the selected code.
    In case of an experimental benchmark, the reference code is set to "exp".

    Parameters
    ----------
    selected_benchmark : str
        selected benchmark
    ref_lib : str
        selected reference library
    status : Status
        status object describing the available data from JADE runs

    Returns
    -------
    str
        selected reference code
    """
    if ref_lib == "exp":
        selected_code = "exp"
    else:
        code_options = status.get_codes(selected_benchmark, ref_lib)
        selected_code = st.selectbox(
            "Select reference code", code_options, index=0, key="code"
        )
    return selected_code


def display_metadata(
    pivot_no_sddr: pd.DataFrame, pivot_sddr: pd.DataFrame, sorted_df: pd.DataFrame
) -> None:
    st.header("Available simulations (no activation)")
    st.dataframe(pivot_no_sddr, use_container_width=True)

    st.header("Available simulations (activation)")
    st.dataframe(pivot_sddr, use_container_width=True)

    st.header("Complete metadata on available simulations")
    st.dataframe(sorted_df, use_container_width=True)


def _split_options(
    options: list[str], divisions: list[int | None] | None
) -> tuple[bool, dict]:
    """Split the options in categories and return a dictionary with the categories as keys."""
    flag_split = False
    ctg_dict = {}

    for i, option in enumerate(options):
        div = divisions[i] if divisions is not None else None
        # Replace protected substrings if present
        for orig, temp in PROTECTED_STRINGS.items():
            option = option.replace(orig, temp)

        # If there is no "-" in the option, add it as a single category with "N.A." as option
        if not "-" in option:
            ctg = option
            option = "N.A."
            # restore original protected substrings
            for orig, temp in PROTECTED_STRINGS.items():
                ctg = ctg.replace(temp, orig)
            safe_add_ctg_to_dict(ctg_dict, [ctg], option)
        else:
            flag_split = True
            if div:
                # if there is a number of divisions specified for this option
                # (different to the number of "-" in the string), split accordingly
                ctgs = option.rsplit("-", maxsplit=divisions[i])
            else:
                # else, if no divisions specified, split normally by "-"
                ctgs = option.split("-")

            # restore original protected substrings
            for i, ctg in enumerate(ctgs):
                for orig, temp in PROTECTED_STRINGS.items():
                    ctgs[i] = ctgs[i].replace(temp, orig)

            safe_add_ctg_to_dict(ctg_dict, ctgs[:-1], ctgs[-1])

    max_depth = find_dict_depth(ctg_dict)
    # if the depth of the options is less than the maximum,
    # add N.A. to an additional layer of options

    for key in ctg_dict:
        # depth_key = find_dict_depth(ctg_dict[key])
        ctg_dict[key] = _recursive_assign_na_option(ctg_dict[key], max_depth)

    return flag_split, ctg_dict


def _recursive_assign_na_option(dict_key, max_depth, counter=0):
    """Recursive function to add "N.A." as the most inner layer of the dictionary of options."""
    counter += 1
    if isinstance(dict_key, list):
        # Only convert if not at max_depth
        if counter < max_depth:
            return {item: ["N.A."] for item in dict_key}
        else:
            return dict_key
    elif isinstance(dict_key, dict):
        for key in dict_key:
            dict_key[key] = _recursive_assign_na_option(
                dict_key[key], max_depth, counter
            )
        return dict_key
    else:
        return dict_key


def _recursive_select_split_option(columns, ctg_dict, labels, selections=None):
    """Recursive function to perform a split selection of the category/options."""
    if selections is None:
        selections = []
    # perform the selection
    with columns[0]:
        if isinstance(ctg_dict, list):
            options_available = ctg_dict
        else:
            options_available = list(ctg_dict.keys())
        # if N.A. is reached, the selection was successful
        if "N.A." in options_available:
            selections.append("N.A.")
            return True, selections
        else:
            index = None

        if isinstance(labels, list):
            label = labels[0]
        else:
            label = 0

        # Build a unique key for the selectbox
        path_key = "-".join(map(str, selections))
        unique_key = f"{label}_{path_key}"

        option_selected = st.selectbox(
            label=label, options=options_available, index=index, key=unique_key
        )
        # add selection to the list
        selections.append(option_selected)

        # if the last column is reached, the selection was successful
        if len(columns) == 1:
            if option_selected is None:
                return False, selections
            return True, selections
        elif option_selected is None:
            return False, selections
        else:
            # recursive function
            return _recursive_select_split_option(
                columns[1:],
                ctg_dict[option_selected],
                labels[1:],
                selections=selections,
            )


def _get_split_selection(
    ctg_dict: dict[str, list[str]], labels: list[str] = None
) -> str | None:
    """perform a split selection of the category/options and return the full option selected."""
    max_depth = find_dict_depth(ctg_dict) + 1
    columns = st.columns(max_depth)
    with columns[0]:
        if isinstance(labels, list) and len(labels) >= max_depth:
            label = labels[0]
        elif labels is None:
            label = 0
        elif isinstance(labels, str):
            label = labels
            labels = [label] + [" " for i in range(max_depth - 1)]
        else:
            raise ValueError("There is a problem with the selection labels")

        # Build a unique key for the selectbox
        depth = max_depth - len(columns)
        unique_key = f"{label}_{depth}"

        ctg_selected = st.selectbox(
            f"Select {label}",
            list(ctg_dict.keys()),
            key=unique_key,
            index=None,
        )
    if ctg_selected:
        success, selections = _recursive_select_split_option(
            columns[1:], ctg_dict[ctg_selected], labels[1:], selections=[ctg_selected]
        )
    else:
        success = False

    if success:
        full_option = selections[0]
        for selection in selections[1:]:
            if selection != "N.A.":
                full_option = full_option + "-" + selection
    else:
        full_option = None

    return full_option


def select_tally(
    selected_benchmark: str, ref_lib: str, selected_code: str, processor: Processor
) -> str:
    """Create a selectbox for the tally selection and return the selected value.

    Parameters
    ----------
    selected_benchmark : str
        selected benchmark
    ref_lib : str
        selected reference library
    selected_code : str
        selected reference code
    processor : Processor
        processor object to get the available tallies

    Returns
    -------
    str
        selected tally
    """
    tallies_options = processor.get_available_tallies(
        selected_benchmark,
        ref_lib,
        selected_code,
    )

    divisions = []
    for i, tally in enumerate(tallies_options):
        try:
            divisions.append(
                processor.params[selected_benchmark][tally]["tally_options_divisions"]
            )
        except KeyError:
            divisions = None
            break
            # If one of the tallies_options does not have divisions, this benchmark will
            # not have any general tallies and, therefore, none of its tallies_options
            # will have the "tally_options_divisions" key associated.

    flag_split, ctg_dict = _split_options(tallies_options, divisions=divisions)

    # Check if there are labels for the tally options
    try:
        labels = processor.params[selected_benchmark]["general"]["tally_options_labels"]
    except KeyError:
        labels = "tally"

    if flag_split:
        tally = _get_split_selection(ctg_dict, labels)
    else:
        if isinstance(labels, list):
            labels = labels[0]
        tally = st.selectbox(
            "Select " + labels, tallies_options, index=None, key="tally"
        )
    return tally


def main():
    # Configure layout of page, must be first streamlit call in script
    st.set_page_config(layout="wide")

    status, processor = get_status_processor()

    # Get available benchmarks
    available_benchmarks = processor.get_available_benchmarks()

    # -- Application --
    # initialization of app state
    if "metadata_available" not in st.session_state:
        st.session_state.metadata_available = False
        st.session_state.metadata_df = None

    tab_plot, tab_info = st.tabs(["Plot", "Info"])

    with tab_plot:
        col01, col02 = st.columns([0.9, 0.1])
        with col01:
            st.title("JADE results interactive plotter")
        with col02:
            st.image(r"jadewa/assets/Jade.png", width=75)

        col1, col2 = st.columns([0.4, 0.6])
        with col1:
            # first select the benchmark
            selected_benchmark = select_benchmark(available_benchmarks)

            # select the libraries for the selected benchmark
            if selected_benchmark:
                ref_lib = select_ref_lib(selected_benchmark, status)
            else:
                ref_lib = None

            # Select the reference code
            if selected_benchmark and ref_lib:
                selected_code = select_ref_code(selected_benchmark, ref_lib, status)
            else:
                selected_code = None

            # select the tally
            if selected_benchmark and ref_lib and selected_code:
                tally = select_tally(
                    selected_benchmark, ref_lib, selected_code, processor
                )
            else:
                tally = None

        with col2:
            # Radio button to select plot type as ratio or not
            ratio_button = st.radio(
                "Plot type", ["Absolute", "Ratio"], index=1, horizontal=True
            )
            if ratio_button == "Ratio":
                ratio = True
            else:
                ratio = False

            # and finally plot!
            if selected_benchmark and ref_lib and tally:
                fig = processor.get_plot(
                    selected_benchmark,
                    ref_lib,
                    selected_code,
                    tally,
                    ratio=ratio,
                )
            else:
                fig = None

            if fig:
                plotly_chart = st.plotly_chart(fig, use_container_width=True)

            expander = st.expander(
                "Select specific libraries across benchmarks.",
                expanded=False,
            )

            with expander:
                st.write(
                    "Select the checkboxes for the libraries to display in the plot. If none are selected, the latest version of each library will be plotted. If a selected library is unavailable for the selected benchmark, its data won't be plotted."
                )
                libs = LIB_NAMES

                # Create checkboxes for all the libraries in LIB_NAMES
                checks = []
                # Fix a maximum of 6 checkboxes per row
                for i in range(0, int(len(libs) / 6)):
                    checks.append(st.columns(6))
                if len(libs) % 6 != 0:
                    checks.append(st.columns(int(len(libs) % 6)))

                # Keep track of the selected libraries
                clicks = list(range(0, len(libs)))
                for i in range(0, len(checks)):
                    for j in range(0, len(checks[i])):
                        with checks[i][j]:
                            clicks[i * 6 + j] = st.checkbox(
                                libs[i * 6 + j], key=libs[i * 6 + j]
                            )

                # The checkboxes will be used as a reference to plot if at least 1 library is selected
                checkbox_selected = False
                if any(clicks):
                    checkbox_selected = True

                if fig and checkbox_selected:
                    # List the selected libraries
                    selected_libs = [libs[i] for i, _ in enumerate(clicks) if clicks[i]]
                    # Apply the selection to the plot legend
                    select_visible_libs(fig, selected_libs)
                    # Update the plot
                    plotly_chart.plotly_chart(fig)

    with tab_info:
        # If the metadata is not available, show the button to compute it
        if not st.session_state.metadata_available:
            # If information have not been computed yet, do it
            if st.button(
                "Compute info on available results",
                key="compute_metadata",
                type="primary",
                disabled=st.session_state.metadata_available,
            ):
                # If the button is pressed, compute the metadata
                st.write("Computing metadata on available results...")
                status.get_metadata_df()
                st.session_state.metadata_available = True
                st.session_state.metadata_df = status.metadata_df

        if st.session_state.metadata_available:
            sorted_df, pivot_sddr, pivot_no_sddr = get_info_dfs(
                st.session_state.metadata_df
            )
            display_metadata(pivot_no_sddr, pivot_sddr, sorted_df)


if __name__ == "__main__":
    main()
