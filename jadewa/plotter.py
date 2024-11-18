import re

import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from plotly.graph_objects import Figure

from jadewa.utils import roman_to_arabic


def get_figure(
    plot_type: str,
    data: pd.DataFrame,
    keyargs: dict,
    y_axis_format: str = False,
    x_axis_format: str = False,
) -> Figure:
    """Get a plotly figure depending on the plot type requested

    Parameters
    ----------
    plot_type : str
        one of the supported plot types
    data : pd.DataFrame
        data to be plotted
    keyargs : dict
        to be passed directly to the plotly express function
    y_axis_format : str, optional
        dictionary of options for the y axis
    x_axis_format : str, optional
        dictionary of options for the x axis

    Returns
    -------
    Figure
        plotly Figure

    Raises
    ------
    ValueError
        if the plot type is not supported
    """

    if plot_type == "step":
        fig = _plot_step(data, **keyargs)
    elif plot_type == "scatter":
        fig = _plot_scatter(data, **keyargs)
    elif plot_type == "grouped_bar":
        fig = _plot_grouped_bars(data, **keyargs)
    else:
        raise ValueError(f"Plot type '{plot_type}' not supported")

    # Check for the most recent version of the corresponding library and deselect the
    # older versions from the plot legend
    _deselect_old_libs(fig)

    if x_axis_format:
        fig.update_xaxes(**x_axis_format)
    if y_axis_format:
        fig.update_yaxes(**y_axis_format)

    # fig.update_yaxes(tickformat=y_tickformat)
    # if x_tickformat is not None:
    #     fig.update_xaxes(tickformat=x_tickformat)

    # fig.update_layout(
    #     xaxis=dict(
    #         tickmode="array",
    #         tickvals=[1, 3, 5, 7, 9, 11],
    #         ticktext=["One", "Three", "Five", "Seven", "Nine", "Eleven"],
    #     )
    # )

    return fig


def _plot_step(data: pd.DataFrame, **keyargs) -> Figure:
    fig = px.line(
        data, **keyargs, color="label", template="plotly_white", line_shape="hv"
    )
    # Experimental data usually have siginificant error that should be traced
    experimental_data = data[data["label"] == "experiment-experiment"]
    if len(experimental_data) > 0:
        x = experimental_data[keyargs["x"]].values
        y = experimental_data[keyargs["y"]].values
        y_upper = y + y * experimental_data["Error"].values
        y_lower = y - y * experimental_data["Error"].values

        fig.add_trace(
            go.Scatter(
                name="exp upper bound",
                x=x,
                y=y_upper,
                # mode='lines',
                line_shape="hv",
                # marker=dict(color="#444"),
                line=dict(width=0),
                showlegend=False,
            )
        )
        hexcol = px.colors.qualitative.Plotly[0].strip("#")
        rgb = list(int(hexcol[i : i + 2], 16) for i in (0, 2, 4))
        rgba = f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.2)"
        fig.add_trace(
            go.Scatter(
                name="exp lower Bound",
                x=x,
                y=y_lower,
                # marker=dict(color="#444"),
                line=dict(width=0),
                # mode="lines",
                line_shape="hv",
                fillcolor=rgba,
                fill="tonexty",
                showlegend=False,
            )
        )
    return fig


def _plot_scatter(data: pd.DataFrame, **keyargs) -> Figure:
    fig = px.scatter(
        data,
        **keyargs,
        color="label",
        template="plotly_white",
        error_y=data["Error"] * data[keyargs["y"]],
        opacity=0.7,
    )
    return fig


def _plot_grouped_bars(data: pd.DataFrame, **keyargs) -> Figure:
    fig = px.bar(
        data, **keyargs, color="label", template="plotly_white", barmode="group"
    )
    return fig


def _deselect_old_libs(fig: Figure) -> None:
    """
    Check for the most recent version of the corresponding library and deselect
    the older versions from the plot legend.

    Parameters
    ----------
    fig : Figure
        figure containing the traces to be processed.

    Returns
    -------
    None
    """
    libraries = {"traces": [], "lib_name": [], "vers1": [], "vers2": []}
    for trace in fig.data:
        if (
            isinstance(trace, (go.Scatter, go.Bar))
            and trace.name != "experiment-experiment"
            and bool(re.search("-", trace.name))
        ):
            # Obtain the trace name and separate the full library+version name
            # (e.g "FENDL 3.2b") from the software used to compute it (e.g "mcnp")
            libraries["traces"].append(trace)
            full_lib = libraries["traces"][-1].name.split("-")[0]

            # Extract the library name (e.g "FENDL") and version (e.g "3.2b") from the trace name
            # For the version, divide in two components (e.g "3.2b" -> "3" and "2b")
            if libraries["traces"][-1].name.split("-")[1] == "d1s":
                lib_name = full_lib.split(" ")[1]
                lib_name = lib_name.replace("(", "")
                vers1, vers2 = full_lib.split(" ")[2].split("+")[0].split(".")
            else:
                lib_name = full_lib.split(" ")[0]
                try:
                    vers1, vers2 = full_lib.split(" ")[1].split(".")
                except ValueError:
                    vers1 = full_lib.split(" ")[1]
                    vers2 = "0"

            # Remove any letters from the second part of the version number (e.g "2b" -> "2")
            vers2 = re.sub(r"[a-zA-Z]", "", vers2)

            # Convert the roman numbers in the library version to arabic numbers (e.g "VIII" -> "8")
            if bool(re.search(r"\d", vers1)):
                pass
            else:
                vers1 = roman_to_arabic(vers1)

            # Find the first index of lib_name in libraries["lib_name"] where the trace is not "legendonly"
            idx = next(
                (
                    i
                    for i, x in enumerate(libraries["lib_name"])
                    if x == lib_name and libraries["traces"][i].visible != "legendonly"
                ),
                None,
            )

            # Compare the trace corresponding to the obtained index with the current
            # trace and deselect the older version from the plot legend
            if idx is not None and trace.visible != "legendonly":
                # Compare the first part of the version number (e.g "3" in "3.2b")
                if vers1 > libraries["vers1"][idx]:
                    fig.update_traces(
                        visible="legendonly",
                        selector={"name": libraries["traces"][idx].name},
                    )
                # If the first part of the version is the same, compare the second part
                # of the version number (e.g "2" in "3.2b")
                elif vers1 == libraries["vers1"][idx]:
                    if vers2 > libraries["vers2"][idx]:
                        fig.update_traces(
                            visible="legendonly",
                            selector={"name": libraries["traces"][idx].name},
                        )
                    elif vers2 < libraries["vers2"][idx]:
                        fig.update_traces(
                            visible="legendonly",
                            selector={"name": libraries["traces"][-1].name},
                        )
                elif vers1 < libraries["vers1"][idx]:
                    fig.update_traces(
                        visible="legendonly",
                        selector={"name": libraries["traces"][-1].name},
                    )

            # Update the libraries dictionary with the trace name, library name and version
            libraries["lib_name"].append(lib_name)
            libraries["vers1"].append(vers1)
            libraries["vers2"].append(vers2)
