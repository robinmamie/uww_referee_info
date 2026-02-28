import pandas as pd

import csv
import pypdf
import re
import requests
import sys

from bs4 import BeautifulSoup
from datetime import datetime
from tqdm import tqdm

def download_referee_list_link() -> str:
    soup = BeautifulSoup(get_url('https://uww.org/development/referees').content, "html.parser")
    for link in soup.find_all('a'):
        if "Referees' list" in link.text and 'Beach' not in link.text and 'Grappling' not in link.text:
            pdf_link = link.get('href')
            pdf_file = get_url(pdf_link)
            filename = 'list.pdf'
            with open(filename, 'wb') as f:
                f.write(pdf_file.content)
                return filename


def extract_license_numbers_from_pdf(only_rcm = False) -> list[int]:
    filename = download_referee_list_link()
    # Read PDF content
    reader = pypdf.PdfReader(filename)
    contents = '\n'.join([page.extract_text() for page in reader.pages])
    # Only keep RCM if needed
    if only_rcm:
        contents = '\n'.join([line for line in contents.split('\n') if "RCM" in line])
    # Split lines, keep only two last words
    lines = [line.strip().split()[-2:] for line in contents.split('\n') if line.strip()]
    # Check whether the last word is a number between 1 and 7 digits
    numbers_raw = [line for line in lines if len(line) == 2 and re.match(r'^\d{1,7}$', line[1])]
    # Remove instances where the first word is a number 
    numbers_raw = [line for line in numbers_raw if not (re.match(r'^\d{2}$', line[1]) and re.match(r'^\d*$', line[0]))]
    # Remove title to exclude CURRENT_YEAR
    numbers_raw = [line for line in numbers_raw if line[0] != 'FOR']
    # Joining strings into valid numbers
    license_numbers = [(int(''.join(line)) if re.match(r'^\d*$', line[0]) else int(line[1])) for line in numbers_raw]

    # Add RAB members' numbers if needed
    rab = []
    if not only_rcm:
        rab = [4236, 2525]

    return rab + license_numbers


def get_url(url: str) -> str:
    attempts_left = 5
    while attempts_left > 0:
        try:
            return requests.get(url)
        except:
            attempts_left -= 1
    raise Exception(f"Could not reach {url} after 5 attempts.")


def get_referee_info_from_athena(license_numbers: list[int]) -> list[dict]:
    referees = []
    for license_number in tqdm(license_numbers):
        referee = {'id_number': license_number}
        athena_link = f"https://athena.uww.org/p/{license_number}"
        page = get_url(athena_link)
        soup = BeautifulSoup(page.content, "html.parser")
        if len(soup.find_all("h1")) > 1:
            # Parse only valid, common pages
            referee['name'] = soup.find_all("h1")[1].text.split('(')[0].strip()
            referee['sex'] = soup.find_all("h1")[1].text.split('(')[-1].split(')')[0].upper()
            referee['country'] = ' '.join(soup.find("h4").text.split()).split(' - ')[1].strip()
            category = soup.find('span',  {'class': 'label-referee'})
            if category and 'Olympic styles' in category.text:
                referee['category'] = category.text.split()[-1]
            else:
                referee['category'] = None
            referee['birthdate'] = datetime.strptime(' '.join(soup.find("h4").text.split()).split(' - ')[0], "%b %d, %Y")
            img_tag = soup.find_all("img")
            referee['photo'] = img_tag[1]["src"] if len(img_tag) > 1 else ''
            activity_field = soup.find('div', {'class': 'alert'})
            activity_field_text = activity_field.text if activity_field else ''
            referee['activity'] = "ACTIVE" if "Active referee license" in activity_field_text else "INACTIVE"
            referees.append(referee)
    return referees


def make_hyperlink(value: str) -> str:
    return f'=HYPERLINK("{value}")'


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


def save_info_to_file(referees: list[dict]) -> None:
    for referee in tqdm(referees):
        referee['birthdate'] = referee['birthdate'].strftime('%Y-%m-%d')
    with open('uww_referees.csv', 'w+') as f:
        writer = csv.DictWriter(f, fieldnames=referees[0].keys())
        writer.writeheader()
        writer.writerows(referees)

    create_xlsx('uww_referees.csv')


def get_international_referees_info() -> None:
    license_numbers = extract_license_numbers_from_pdf()
    referees = get_referee_info_from_athena(license_numbers)
    # Extract RCM information from PDF
    for rcm in extract_license_numbers_from_pdf(True):
        [ref for ref in referees if ref['id_number'] == rcm][0]['category'] = 'IS-RCM'
    save_info_to_file(referees)


def main() -> None:
    get_international_referees_info()


if __name__ == '__main__':
    sys.exit(main())
