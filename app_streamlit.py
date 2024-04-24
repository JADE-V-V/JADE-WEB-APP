"""Main streamlit app entry point.
"""

import streamlit as st
from jadewa.status import Status
from jadewa.processor import Processor
from jadewa.utils import (
    get_mat_iso_code,
    get_pretty_mat_iso_names,
    get_lib_suffix,
    get_pretty_lib_names,
)

# Get list of CSV files in current directory
OWNER = "JADE-V-V"
REPO = "JADE-RAW-RESULTS"
BRANCH = "main"


# Initialize status and processor
@st.cache_data
def get_status_processor():
    """Get the status and processor objects"""
    session_status = Status.from_github(OWNER, REPO, branch=BRANCH)
    session_processor = Processor(session_status)
    return session_status, session_processor


def main():
    # Configure layout of page, must be first streamlit call in script
    st.set_page_config(layout="wide")

    status, processor = get_status_processor()

    # Get available benchmarks
    available_benchmarks = status.get_benchmarks()

    # -- Application --
    col01, col02 = st.columns([0.9, 0.1])
    with col01:
        st.title("JADE results interactive plotter [ALPHA]")
    with col02:
        st.image(r"jadewa/assets/Jade.png", width=75)

    col1, col2 = st.columns([0.4, 0.6])
    with col1:
        # first select the benchmark
        selected_benchmark = st.selectbox(
            "Select benchmark", available_benchmarks, index=None, key="benchmark"
        )

        # get the libraries for the selected benchmark
        if selected_benchmark:
            lib_options = status.get_libraries(selected_benchmark)
            #  get pretty names for the libraries
            lib_options = get_pretty_lib_names(lib_options)
            ref_lib = st.selectbox(
                "Select reference library", lib_options, index=None, key="lib"
            )
        else:
            ref_lib = None

        # Select the reference code
        if selected_benchmark and ref_lib:
            code_options = status.get_codes(selected_benchmark, get_lib_suffix(ref_lib))
            selected_code = st.selectbox(
                "Select reference code", code_options, index=0, key="code"
            )
        else:
            selected_code = None

        # optional, get the isotope or material for the selected benchmark
        if selected_benchmark == "Sphere":
            if ref_lib and selected_code:
                isotope_material_options = processor.get_available_isotopes_materials(
                    selected_benchmark, get_lib_suffix(ref_lib), selected_code
                )
                # get pretty names
                pretty_options = get_pretty_mat_iso_names(isotope_material_options)

                isotope_material = st.selectbox(
                    "Select isotope or material",
                    pretty_options,
                    index=None,
                    key="isotope",
                )
        else:
            isotope_material = None

        # select the tally
        if selected_benchmark and ref_lib and selected_code:
            tallies_options = processor.get_available_tallies(
                selected_benchmark,
                get_lib_suffix(ref_lib),
                selected_code,
            )
            tally = st.selectbox(
                "Select tally", tallies_options, index=None, key="tally"
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
            if selected_benchmark == "Sphere":
                if isotope_material:
                    fig = processor.get_plot(
                        selected_benchmark,
                        get_lib_suffix(ref_lib),
                        selected_code,
                        tally,
                        # use the raw name
                        isotope_material=get_mat_iso_code(isotope_material),
                        ratio=ratio,
                    )
                else:
                    fig = None
            else:
                fig = processor.get_plot(
                    selected_benchmark,
                    get_lib_suffix(ref_lib),
                    selected_code,
                    tally,
                    ratio=ratio,
                )
        else:
            fig = None

        if fig:
            st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
