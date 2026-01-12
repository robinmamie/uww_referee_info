#!/bin/bash

time_stamp=$(date +%Y-%m-%d)
base_archive_folder="referees/history"
archive_folder="${base_archive_folder}/${time_stamp}"
mkdir -p ${archive_folder}

echo "Checking (${time_stamp})"

python uww_referees.py
python graph.py

montage stats_IS.png stats_I.png stats_II.png stats_III.png -mode Concatenate -tile 1x stats.png

cp uww_referees.xlsx uww_referees.csv list.pdf stats.png ${archive_folder}

snd_last_archive_folder=$(ls -- ${base_archive_folder}/*/uww_referees.csv | tail -n 2 | head -n 1)
ln -sfn ${snd_last_archive_folder} last.csv
last_diff=$(diff last.csv uww_referees.csv)

if  [[ -z ${last_diff} ]]; then
   echo 'No diff, deleting new folder.'
   rm -rf ${archive_folder}
else
   echo 'New information available.'
   python update_history.py
   cp changes_*.csv ${archive_folder}
   echo ${time_stamp} > ${base_archive_folder}/.last
fi
