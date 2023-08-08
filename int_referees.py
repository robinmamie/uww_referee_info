import csv
import PyPDF2
import re
import requests
import sys

from bs4 import BeautifulSoup
from collections import defaultdict
from datetime import datetime, date
from tqdm import tqdm


def extract_license_numbers_from_pdf(filename):
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

    return license_numbers


def fetch_referee_page(url):
    return requests.get(url)


def get_referee_info_from_athena(license_numbers):
    referees = []
    for license_number in tqdm(license_numbers):
        referee = {'id_number': license_number}
        athena_link = f"https://uww.io/r/{license_number}"
        page = fetch_referee_page(athena_link)
        soup = BeautifulSoup(page.content, "html.parser")
        referee['name'] = soup.find_all("h1")[1].text.split('(')[0].strip()
        referee['sex'] = soup.find_all("h1")[1].text.split('(')[-1].split(')')[0].upper()
        referee['country'] = ' '.join(soup.find("h4").text.split()).split(' - ')[1].strip()
        referee['category'] = soup.find('span',  {'class': 'label-referee'}).text.split()[-1]
        referee['birthdate'] = datetime.strptime(' '.join(soup.find("h4").text.split()).split(' - ')[0], "%b %d, %Y")
        img_tag = soup.find_all("img")
        referee['photo'] = img_tag[1]["src"] if len(img_tag) > 1 else ''
        referee['athena'] = athena_link
        referees.append(referee)
    return referees


def save_info_to_file(referees):
    for referee in tqdm(referees):
        referee['birthdate'] = referee['birthdate'].strftime('%Y-%m-%d')
    with open('int_referees.csv', 'w+') as f:
        writer = csv.DictWriter(f, fieldnames=referees[0].keys())
        writer.writeheader()
        writer.writerows(referees)


def get_international_referees_info(filename):
    license_numbers = extract_license_numbers_from_pdf(filename)
    referees = get_referee_info_from_athena(license_numbers)
    save_info_to_file(referees)


def main():
    get_international_referees_info(sys.argv[1])


if __name__ == '__main__':
    sys.exit(main())
