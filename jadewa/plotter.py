from plotly.graph_objects import Figure
import plotly.express as px
import pandas as pd


def get_figure(
    plot_type: str,
    data: pd.DataFrame,
    keyargs: dict,
    y_tickformat: str = ".2e",
    x_tickformat: str = None,
) -> Figure:
    """Get a plotly figure depending on the plot type requested

    Parameters
    ----------
    plot_type : str
        one of the supported plot types
    data : pd.DataFrame
        data to be plotted
    **keyargs : dict
        to be passed directly to the plotly express function
    y_tickformat : str, optional
        x-axis tickformat, by default "e"
    x_tickformat : str, optional
        y-axis tickformat, by default None

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
    else:
        raise ValueError(f"Plot type '{plot_type}' not supported")

    fig.update_yaxes(tickformat=y_tickformat)
    if x_tickformat is not None:
        fig.update_xaxes(tickformat=x_tickformat)

    return fig


def _plot_step(data: pd.DataFrame, **keyargs) -> Figure:
    fig = px.line(
        data, **keyargs, color="label", template="plotly_white", line_shape="hv"
    )
    return fig


def _plot_scatter(data: pd.DataFrame, **keyargs) -> Figure:
    fig = px.scatter(
        data,
        **keyargs,
        color="label",
        template="plotly_white",
        error_y=data["Error"] * data[keyargs["y"]],
    )
    return fig
