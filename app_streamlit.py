"""Main streamlit app entry point.
"""

import streamlit as st
from jadewa.status import Status
from jadewa.processor import Processor

# Get list of CSV files in current directory
OWNER = "JADE-V-V"
REPO = "JADE-RAW-RESULTS"
BRANCH = "main"

# Initialize status and processor
status = Status.from_github(OWNER, REPO, branch=BRANCH)
processor = Processor(status)

# Get available benchmarks
available_benchmarks = status.get_benchmarks()

# -- Application --
st.set_page_config(layout="wide")
st.title("JADE results interactive plotter [ALPHA]")
col1, col2 = st.columns([0.4, 0.6])

with col1:
    # first select the benchmark
    selected_benchmark = st.selectbox(
        "Select benchmark", available_benchmarks, index=None
    )

    # get the libraries for the selected benchmark
    if selected_benchmark:
        lib_options = status.get_libraries(selected_benchmark)
        ref_lib = st.selectbox("Select reference library", lib_options, index=None)
    else:
        ref_lib = None

    # optional, get the isotope or material for the selected benchmark
    if selected_benchmark == "Sphere":
        if ref_lib:
            isotope_material_options = processor.get_available_isotopes_materials(
                selected_benchmark, ref_lib, "mcnp"
            )

            isotope_material = st.selectbox(
                "Select isotope or material", isotope_material_options, index=None
            )
    else:
        isotope_material = None

    # select the tally
    if selected_benchmark and ref_lib:
        tallies_options = processor.get_available_tallies(
            selected_benchmark, ref_lib, "mcnp"
        )
        tally = st.selectbox("Select tally", tallies_options, index=None)

    # and finally plot!
    if selected_benchmark and ref_lib and tally:
        if selected_benchmark == "Sphere":
            if isotope_material:
                fig = processor.get_plot(
                    selected_benchmark,
                    ref_lib,
                    tally,
                    isotope_material=isotope_material,
                )
            else:
                fig = None
        else:
            fig = processor.get_plot(selected_benchmark, ref_lib, tally)
    else:
        fig = None

    st.image(r"jadewa/assets/Jade.png", width=200)

with col2:
    if fig:
        st.plotly_chart(fig, use_container_width=True)
