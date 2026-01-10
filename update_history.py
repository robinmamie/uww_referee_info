import country_converter as coco

import glob
import json
import os
import sys

from bs4 import BeautifulSoup
from csv_diff import load_csv, compare
from datetime import datetime
from tqdm import tqdm

base_path = "referees"
date = datetime.today().strftime('%Y-%m-%d')

def get_ref_path(id_number: str) -> str:
    return f"{base_path}/{int(id_number)}.csv"

def write_csv(path, fieldnames, rows: list, append=True):
    mode = 'a' if append else 'w'
    with open(path, mode, newline='') as csvfile:
        writer = DictWriter(csvfile, fieldnames=fieldnames)
        if not append:
            writer.writeheader()
        for row in rows:
            writer.writerow(row)


def create_referee(ref: dict, date: str) -> None:
    ref['timestamp'] = date
    path = get_ref_path(ref['id_number'])
    if os.path.exists(path):
        raise Exception(f"Trying to create a referee that already exists: {ref}")
    fieldnames = ref.keys()
    write_csv(path, fieldnames, [ref], append=False)
    
def update_referee(ref: dict, date: str) -> None:
    ref['timestamp'] = date
    path = get_ref_path(ref['id_number'])
    if not os.path.exists(path):
        raise Exception(f"Trying to update a referee that does not exist: {ref}")
    fieldnames = ref.keys()
    write_csv(path, fieldnames, [ref], append=True)


def retire_referee(ref: dict, date: str) -> None:
    ref['timestamp'] = date
    ref['activity'] = 'RETIRED'
    path = get_ref_path(ref['id_number'])
    if not os.path.exists(path):
        raise Exception(f"Trying to retire a referee that does not exist: {ref}")
    fieldnames = ref.keys()
    write_csv(path, fieldnames, [ref], append=True)


def update_index(current: dict) -> None:
    with open('referees/referees.json') as f:
        referee_index = json.load(f)
    for _, ref in current.items():
        referee_index[ref['name']] = int(ref['id_number'])
    with open('referees/referees.json', 'w') as f:
        json.dump(referee_index, f)
        
    with open('referees/referees-inv.json') as f:
        referee_index = json.load(f)
    for _, ref in current.items():
        referee_index[int(ref['id_number'])] = {
            'name': ref['name'],
            'country': ref['country'],
        }
    with open('referees/referees-inv.json', 'w') as f:
        json.dump(referee_index, f)


def create_xlsx(current_path_file: str) -> None:
    df = pd.read_csv(current_path_file)
    df['photo'] = df['photo'].apply(make_hyperlink)
    df['athena'] = df['id_number'].apply(lambda idn: make_hyperlink(f"https://athena.uww.org/p/{idn}"))

    with pd.ExcelWriter(current_path_file.replace('.csv', '.xlsx')) as writer:
        df.to_excel(writer, sheet_name='UWW referees', index=False, na_rep='')
        for column in df:
            column_length = max(df[column].astype(str).map(len).max(), len(column))
            col_idx = df.columns.get_loc(column)
            writer.sheets['UWW referees'].set_column(col_idx, col_idx, column_length)


def main() -> None:
    old = load_csv(open("last.csv"), key="id_number")
    current = load_csv(open("uww_referees.csv"), key="id_number")
    diff = compare(old, current)
    date = new_folder

    update_index(current)

    old_diff = []
    new_diff = []

    for changes in diff['changed']:
        id_number = changes['key']
        ref = current[id_number]
        update_referee(dict(ref), date)
        old_diff.append(old[id_number])
        new_diff.append(ref)
    for ref in diff['added']:
        if os.path.exists(get_ref_path(ref['id_number'])):
            update_referee(dict(ref), date)
        else:
            create_referee(dict(ref), date)
        new_diff.append(ref)
    for ref in diff['removed']:
        retire_referee(dict(ref), date)
        old_diff.append(ref)

    fieldnames = current['41846'].keys()
    write_csv("changes_previous_state.csv", fieldnames, old_diff, append=False)
    write_csv("changes_current_state.csv", fieldnames, new_diff, append=False)


if __name__ == '__main__':
    sys.exit(main())
