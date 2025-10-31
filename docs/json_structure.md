# JSON configuration files structure

Adding a new benchmark to be supported by the web app is as easy as to add a .json file in the [resources](../jadewa/resources/) folder. The name of the file should be the same as the one used in the [raw data repository](https://github.com/JADE-V-V/JADE-RAW-RESULTS). In such file, a structure like the following should be added for each of the tallies that are to be supported:

```json
{
    ...
"Reaction Rates - S32 (n,p) P32": {
    "result": "ASPIS-PCA-Replica_S Reaction Rate S",
    "substitutions": {
            "Cells": "Shielding thickness [cm]",
            "Value": "C/E (Reaction rate)"
        },
        "plot_type": "scatter",
        "plot_args": {
            "x": "Shielding thickness [cm]",
            "y": "C/E (Reaction rate)",
            "log_x": false,
            "log_y": false
        },
        "y_axis_format": {
            "tickformat": ".2e"
        },
        "only_ratio": true
    },
    ...
}
```

where the key of the tally dictionary is the name that will appear on the web app tally selection. If a "-" is contained, it will consider it a couple `category - option` and will split the selection into two parts (or more). This is particularly useful for benchmarks with a huge list of available tallies which more often than not are just combination of different configuration of the same benhcmark (i.e. a change in geometry or materials) and actual available tallies.

At the same tally level, a `"general"` tally can be optionally specified. This contains parameters that are not related to the rendering of the single tally result, but are applicable to the benchmark itself. The only options available for the moment are:
<dl>
  <dt>tally_options_labels</dt>
  <dd>This accepts a list of labels that will be used to give additional information in case the tally selection was to be split into subcategories</dd>
  <dt>generic_tallies</dt>
  <dd>This allows to define generic tallies instead of specific ones. more details can be found below in the tally_name option</dd>
</dl>

If _generic_tallies_ has been set to _true_, it is also possible to define "generic" tallies, like for the Sphere SDDR benchmark. This is to be used when different versions of the same benchmarks are run (for instance, different isotopes in the sphere) but they all have the same tallies. It is not useful to individually include all the tallies for each isotope (they can be hundreds) in the .json file, hence, a generic tally is defined. As an example, if all .csv results are provided as "benchmark_option1-option2 tallyname.csv", then a generic tally should be provided with key = "{} - {} - quantity name". Internally, the code, during the initialization of the Processor class will substitute each "{}" for one of the options and add a tally config for each combination of option1 and option2 found across the .csv.

The following, instead, are the available options for each tally configuration.

## Mandatory configuration options

<dl>
  <dt>result</dt>
  <dd> it can either be a string of a list of strings. If it's a single string, it is interpreted as the name of the .csv file in the raw data repository that contains the data to plot. If it's a list of strings, it corresponds to the group of .csv files in the raw data repository whose data will be plotted together.
  If a generic tally is being defined and the corresponding .csv files follow the naming convention "benchmark_option1-option2 tallyname.csv", only the tallyname should be specified for this configuration option.
  The same .csv file can be used across different tally dictionaries.<dd>  
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
  <dt>subset</dt>
  <dd>a list [column_name, value] is expected. The effect is that from the total raw data table, only the rows that contain value in the specified column will be retained for plotting.</dd>
  <dt>only_ratio</dt>
  <dd>forces the plot always to be C/E (ratio). This is sometimes useful for
  some of the experimental benchmarls where absolute values are not that important.</dd>
</dl>
