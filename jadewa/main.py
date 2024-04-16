"""Main app entry point.
"""

import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from jadewa.status import Status
from jadewa.processor import Processor


# Get list of CSV files in current directory
ROOT = r"R:\AC_ResultsDB\Jade\03_JADEv300_root\Tests\Post-Processing\Single_Libraries"


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
status = Status.from_root(ROOT)
processor = Processor(status)
app.title = "JADE plotter"

dropdowns = html.Div(
    children=[
        html.H2("JADE results interactive plotter"),
        dcc.Dropdown(
            id="benchmark-dropdown",
            options=[{"label": i, "value": i} for i in status.get_benchmarks()],
            placeholder="Select a Benchmark",
        ),
        dcc.Dropdown(
            id="reflib-dropdown",
            placeholder="Select reference library",
        ),
        dcc.Dropdown(
            id="isotope_material",
            placeholder="Select the specific isotope or material",
        ),
        dcc.Dropdown(
            id="tally-dropdown",
            placeholder="Select the tally to plot",
        ),
    ]
)

app.layout = html.Div(
    children=[
        dbc.Row(
            [
                dbc.Col(dropdowns, width={"size": 6, "offset": 1}),
                dbc.Col(
                    html.Div(
                        children=html.Img(
                            src=dash.get_asset_url("Jade.png"),
                            style={"width": "100%"},
                        )
                    ),
                    width={"size": 2, "offset": 1},
                ),
                # dbc.Col(html.Div("logo here"), width=6),
            ],
        ),
        dbc.Row(
            html.Div(
                children=[dcc.Graph(id="my-graph")],
                style={"width": "90%", "vertical-align": "middle"},
            )
        ),
    ]
)


@app.callback(
    Output("reflib-dropdown", "options"),
    # Output("yaxis-dropdown", "options"),
    Input("benchmark-dropdown", "value"),
)
def update_lib_dropdown(selected_benchmark: str) -> list[str]:
    if selected_benchmark:
        # Show options for
        options = status.get_libraries(selected_benchmark)
        return options  # , options
    return []  # , []


@app.callback(
    Output("isotope_material", "options"),
    Input("reflib-dropdown", "value"),
    Input("benchmark-dropdown", "value"),
)
def update_isotope_material(selected_lib: str, selected_benchmark: str) -> list[str]:
    if selected_lib and selected_benchmark and selected_benchmark == "Sphere":
        if selected_benchmark == "Sphere":
            options = processor.get_available_isotopes_materials(
                selected_benchmark, selected_lib, "mcnp"
            )
            return options
    return []


@app.callback(
    Output("tally-dropdown", "options"),
    # Output("yaxis-dropdown", "options"),
    Input("benchmark-dropdown", "value"),
    Input("reflib-dropdown", "value"),
)
def update_tally_dropdown(selected_benchmark: str, selected_lib: str) -> list[str]:
    if selected_benchmark and selected_lib:
        # Show options for
        options = processor.get_available_tallies(
            selected_benchmark, selected_lib, "mcnp"
        )
        return options  # , options
    return []  # , []


@app.callback(
    Output("my-graph", "figure"),
    Input("benchmark-dropdown", "value"),
    Input("reflib-dropdown", "value"),
    Input("tally-dropdown", "value"),
    Input("isotope_material", "value"),
)
def update_graph(
    selected_benchmark: str,
    selected_lib: str,
    selected_tally: str,
    isotope_material: str,
):
    if selected_benchmark and selected_lib and selected_tally:
        if selected_benchmark == "Sphere" and isotope_material:
            fig = processor.get_plot(
                selected_benchmark,
                selected_lib,
                selected_tally,
                isotope_material=isotope_material,
            )
        else:
            fig = processor.get_plot(selected_benchmark, selected_lib, selected_tally)
        return fig
    return {}


if __name__ == "__main__":

    app.run_server(debug=True)
