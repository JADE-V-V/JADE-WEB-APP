from plotly.graph_objects import Figure
import plotly.express as px
import pandas as pd


def get_figure(
    plot_type: str,
    data: pd.DataFrame,
    keyargs: dict,
    y_axis_format: str = None,
    x_axis_format: str = None,
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
    else:
        raise ValueError(f"Plot type '{plot_type}' not supported")

    if x_axis_format is not None:
        fig.update_xaxes(**x_axis_format)
    if y_axis_format is not None:
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
