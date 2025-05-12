import re

import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from plotly.graph_objects import Figure


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

    # Check for the most recent version of each corresponding library, select it in the
    # plot legend and deselect the older versions
    if fig:
        # Define the labels for the available libraries in the benchmark
        libraries = [
            trace.name.split("-")[0]
            for trace in fig.data
            if bool(re.search("-", trace.name))
        ]
        # Create a DataFrame with the library names and labels
        df = build_lib_df(libraries)
        # Order the libraries by their name and version number (included in the label)
        df = df.groupby("Library").max()["Label"].values
        # Select the new versions of the libraries in the plot legend and deselect the old ones
        select_visible_libs(fig, df)

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


def get_lib_version(label: str) -> list[str]:
    """Get the library name and version separately from the label
    Parameters
    ----------
    label : str
        label of the library

    Returns
    -------
    list[str]
        list with the library name and version
    """
    return label.split(" ")


def build_lib_df(available_libs: list[str]) -> pd.DataFrame:
    """Build a DataFrame with the library names and labels

    Parameters
    ----------
    available_libs : list[str]
        list of library labels

    Returns
    -------
    pd.DataFrame
        DataFrame with the library names and labels
    """
    rows = []
    for label in available_libs:
        lib_name = get_lib_version(label)[0]
        rows.append((lib_name, label))
    df = pd.DataFrame(rows, columns=["Library", "Label"])
    return df


def select_visible_libs(fig: Figure, df: list) -> None:
    """Select the libraries contained in the list df in the plot legend and deselect the others

    Parameters
    ----------
    fig : Figure
        plotly Figure
    df : list
        list of labels for the libraries to be selected in the plot legend

    Returns
    -------
    None
    """
    for trace in fig.data:
        if trace.name.split("-")[0] in df:
            trace.visible = True
        else:
            trace.visible = "legendonly"
