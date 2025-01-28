import pandas as pd

import csv
import PyPDF2
import re
import requests
import sys

from bs4 import BeautifulSoup
from collections import defaultdict
from datetime import datetime, date
from tqdm import tqdm


def download_referee_list_link() -> str:
    soup = BeautifulSoup(requests.get('https://uww.org/development/referees').content, "html.parser")
    for link in soup.find_all('a'):
        if "Referees' list" in link.text and 'Beach' not in link.text and 'Grappling' not in link.text:
            pdf_link = link.get('href')
            pdf_file = requests.get(pdf_link)
            filename = 'list.pdf'
            with open(filename, 'wb') as f:
                f.write(pdf_file.content)
                return filename


def extract_license_numbers_from_pdf() -> list[int]:
    filename = download_referee_list_link()
    # Read PDF content
    reader = PyPDF2.PdfReader(filename)
    contents = '\n'.join([page.extract_text() for page in reader.pages])
    # Split lines, keep only two last words
    lines = [line.strip().split()[-2:] for line in contents.split('\n') if line.strip()]
    # Check whether the last word is a number between 1 and 3 digits
    numbers_raw = [line for line in lines if len(line) == 2 and re.match(r'^\d{1,3}$', line[1])]
    # Remove instances where the first word is a number 
    numbers_raw = [line for line in numbers_raw if not (re.match(r'^\d{2}$', line[1]) and re.match(r'^\d*$', line[0]))]
    # Joining strings into valid numbers
    license_numbers = [(int(''.join(line)) if re.match(r'^\d*$', line[0]) else int(line[1])) for line in numbers_raw]

    # Add instructors' numbers
    instructors = [
            4236,
            2525,
            4717,
            4729,
            3520,
            4489,
            4443,
            4754,
            4177,
            4734,
            4150,
            3408,
            3231,
    ]

    return instructors + license_numbers


def fetch_referee_page(url: str) -> str:
    return requests.get(url)


def get_referee_info_from_athena(license_numbers: list[int]) -> list[dict]:
    referees = []
    for license_number in tqdm(license_numbers):
        referee = {'id_number': license_number}
        athena_link = f"https://athena.uww.org/p/{license_number}"
        page = fetch_referee_page(athena_link)
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
            activity_field = soup.find('div', {'class': 'alert'})
            activity_field_text = activity_field.text if activity_field else ''
            referee['is_active'] = "Active referee license" in activity_field_text
            img_tag = soup.find_all("img")
            referee['photo'] = img_tag[1]["src"] if len(img_tag) > 1 else ''
            referee['athena'] = athena_link
            referees.append(referee)
    return referees


def make_hyperlink(value: str) -> str:
    return f'=HYPERLINK("{value}")'


def save_info_to_file(referees: list[dict]) -> None:
    for referee in tqdm(referees):
        referee['birthdate'] = referee['birthdate'].strftime('%Y-%m-%d')
    with open('uww_referees.csv', 'w+') as f:
        writer = csv.DictWriter(f, fieldnames=referees[0].keys())
        writer.writeheader()
        writer.writerows(referees)

    df = pd.read_csv('uww_referees.csv')
    df['photo'] = df['photo'].apply(make_hyperlink)
    df['athena'] = df['athena'].apply(make_hyperlink)

    writer = pd.ExcelWriter('uww_referees.xlsx') 
    df.to_excel(writer, sheet_name='UWW referees', index=False, na_rep='')
    
    for column in df:
        column_length = max(df[column].astype(str).map(len).max(), len(column))
        col_idx = df.columns.get_loc(column)
        writer.sheets['UWW referees'].set_column(col_idx, col_idx, column_length)
    
    writer.close()


def get_international_referees_info() -> None:
    license_numbers = extract_license_numbers_from_pdf()
    referees = get_referee_info_from_athena(license_numbers)
    save_info_to_file(referees)


def main() -> None:
    get_international_referees_info()


if __name__ == '__main__':
    sys.exit(main())
