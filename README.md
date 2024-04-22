[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://jade-web-app-q4gmytmvbalfgbgjdnfifr.streamlit.app/)

# JADE-WEB-APP

This is a web application for the visualization of JADE results without the need of installations or simulations. You can accesse the app [here](https://jade-web-app-q4gmytmvbalfgbgjdnfifr.streamlit.app/) or clicking on the streamlit badge at the top of the README.md

The source of data used for the plots are raw .csv file that are produced from [JADE](https://github.com/JADE-V-V/JADE) post-processing of single libraries (or comparisons for experimental benchmarks). Data for the web-application is hosted and mantained [here](https://github.com/JADE-V-V/JADE-RAW-RESULTS) but, if downloaded locally, the app could be set to read the data directly from a local JADE folder structure. This can be achieved changing the line:

```status = Status.from_github(OWNER, REPO, branch=BRANCH)```

in the ``app_streamlit.py`` module to:

```status = Status.from_root('path/to/the/JADE/post-processing/folder/Single_Libraries')```

For additional information contact sc-radiationtransport@f4e.europa.eu.

## Additional instructions for developers

In addition to the requirements that can be found in the [requirements](./requirements.txt) file, the additional python packages are needed for unit testing:

- pytest
- pytest-cov
- pytest-mock

To run the suite of unit tests (and produce a coverage html tree) run:

```pytest --cov=. --cov-report html```