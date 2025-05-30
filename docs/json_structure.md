# JSON configuration files structure

Adding a new benchmark to be supported by the web app is as easy as to add a .json file in the [resources](../jadewa/resources/) folder. The name of the file shoould be the same as the one used in the [raw data repository](https://github.com/JADE-V-V/JADE-RAW-RESULTS). In such file, a structure like the following should be added for each of the tallies that are to be supported:

```json
{
    ...
"W 41": {
    "tally_name": "W - Photon leakage spectrum",
    "substitutions": {
        "Energy": "Energy [MeV]",
        "Value": "Photon leakage spectrum per unit energy [#/cm^2/s/MeV]"
    },
    "plot_type": "step",
    "plot_args": {
        "x": "Energy [MeV]",
        "y": "Photon leakage spectrum per unit energy [#/cm^2/s/MeV]",
        "log_x": true,
        "log_y": true
    },
    "y_axis_format": {"tickformat": ".2e"},
    "compute_per_unit_bin": "Energy"
},
    ...
}
```

where the key of the tally dictionary needs to be the name of the .csv file  in the raw data repository that contains the data to plot.

At the same tally level, a `"general"` tally can be optionally specified. This contains parameters that are not related to the rendering of the single tally result, but are applicable to the benchmark itself. The only options available for the moment are:
<dl>
  <dt>tally_options_labels</dt>
  <dd>This accepts a list of labels that will be used to give additional information in case the tally selection was to be split into subcategories</dd>
  <dt>generic_tallies</dt>
  <dd>This allows to define generic tallies instead of specific ones. more details can be found below in the tally_name option</dd>
</dl>

The following, instead, are the available options for each tally configuration.

## Mandatory configuration options

<dl>
  <dt>tally_name</dt>
  <dd>this is the name that will appear on the web app tally selection. If a "-" is contained, it will consider it a couple `category - option` and will split the selection into two parts (or more). This is particularly useful for benchmarks with a huge list of available tallies which more often than not are just combination of different configuration of the same benhcmark (i.e. a change in geometry or materials) and actual available tallies.
  
  It is also possible to define "generic" tallies like for the Sphere SDDR benchmark (the correspondent general option must be set to true). This is to be used when different version of the same benchmarks
  are run (for instance, different isotopes in the sphere) but they all have 
  the same tallies. It is not useful all the tallies for each isotope (they can be hundreds), hence, a generic tally is defined. As an example, if all .csv results are provided as option1_option2_tallynum, then a generic tally should be provided with key = tallynum and tallyname as "{} - {} - quantity name". Internally, the code, during the initialization of the Processor class will add a tally config for each combination of option1 and option2 found across the .csv</dd>
  <dt>plot_type</dt>
  <dd>at the moment the available plot types are `step`, `scatter` and `grouped_bar`. You can check the webapp directly to have a feeling of how these plots look like.</dd>
  <dt>plot_args</dt>
  <dd>this is the dictionary of options that will be passed directly to the `plotly` native functions. The minimum requirement is to specify at least the `x` and `y` column name to be used for the plot. For a full reference of the available additional options you can check:
  <ul>
  <li><a href=https://plotly.com/python-api-reference/generated/plotly.express.line.html>step options</a> from plotly API reference</li>
  <li><a href=https://plotly.com/python-api-reference/generated/plotly.express.scatter.html>scatter options</a> from plotly API reference. </li> 
  <li><a href=https://plotly.com/python-api-reference/generated/plotly.express.bar>grouped_bar options</a> from plotly API reference. </li>
  </ul>
  </dd>
</dl>


## Recommended configuration options

<dl>
  <dt>substitutions</dt>
  <dd>this is itself a dictionary that maps some column name in the raw .csv data
to be changed to other, more meaningful, names. In fact, the dataframe read from
the .csv will be passed to the `plotly.express` plotter at some point and the
column names will be directly used for x and y labels on the graph.</dd>
</dl>

## Optional configuration options

<dl>
  <dt>y_axis_format and x_axis_format</dt>
  <dd>these parameters allow you to customize the axis properties such as ticks number, labels, labels format, etc. You can see a complete list of the parameters that can be controlled at <a href=https://plotly.com/python/reference/layout/xaxis>this page</a> of the plotly API reference.</dd>
  <dt>compute_lethargy</dt>
  <dd>if set to `true`, all data coming from simulations (that is, not experimental data) will expect an `Energy` column in the raw dataframe and use it to convert the `Value` column (intended as a flux) in a flux per unit lethargy. $\phi_n = \phi_n/\log(E_{n}/E_{n-1})$</dd>
  <dt>compute_per_unit_bin</dt>
  <dd>this parameter allows you to normalize the `Value` column (intended as a flux) from all data coming from simulations (that is, not experimental data) to flux per bin. $\phi_n = \phi_n/(V_{n} - V_{n-1})$. A string containing the name of the x-axis data column in the raw dataframe (e.g `Energy`, `Time`) is expected.</dd>
  <dt>subset</dt>
  <dd>a list [column_name, value] is expected. The effect is that from the total raw data table, only the rows that contain value in the specified column will be retained for plotting.</dd>
  <dt>only_ratio</dt>
  <dd>forces the plot always to be C/E (ratio). This is sometimes useful for
  some of the experimental benchmarls where absolute values are not that important.</dd>
  <dt>sum_by</dt>
  <dd>allow to perform a `grouby().sum()` operation on the result dataframe
  before processing. The grouby is done on the specified column. This operation is done before column name sostitutions. This function assumes
  a Value and Error columns. Value will be re-computed as `grouby().sum()`, 
  Error as the total absolute error divided by the total value. </dd>
</dl>
