# International Referees' Information Extractor

Python script scraping the Olympic Wrestling international referee information from the Athena system.

## Requirements

Install the python requirements:

    pip install -r requirements.txt

## Running

Run the script like so:

    python wrestling_referees.py

This script produces the file `uww_referees.csv`, the result of the parsing/scraping, the same result in an Excel file (`uww_referees.xlsx`) and `list.pdf`, which is the official referees' list downloaded from the UWW website.

The scraping takes a while: the requests were not parallelized to avoid DoSing the Athena system/being IP-banned.

All the referee information is extracted from Athena, so everything is up to date. The PDF file is only there to provide the base license numbers.

The following script:

    python update_referee_cards.py

Updates the database of referees by comparing the last csv file (which must be called `last.csv`) with the one generated with the previous script. It also outputs the `referee_changes.html` file, which lists the diff of the two files in a pretty way.

## Basic graphs

To get basic statistic graphs, run the following file:

    python graph.py

which creates several image files in the folder `img`.

You can concatenate them into one image using imagemagick and the `img/concatenate.sh` script.
