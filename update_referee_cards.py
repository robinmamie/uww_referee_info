import country_converter as coco

import datetime
import os
import sys

from csv_diff import load_csv, compare
from tqdm import tqdm


cc = coco.CountryConverter()
emoji_a = 127462
base_path = "referees"
history_header = '<button id="toggle">Show History</button>\n<div id="history">\n'
date = datetime.datetime.today().strftime('%Y-%m-%d')

with open("uww_card.html") as f:
    card = f.read()
with open("uww_referee.html") as f:
    page = f.read()


def get_emoji_flag(country2: str):
    a = "&#x" + format(emoji_a + ord(country2[0]) - ord("A"), "X")
    b = "&#x" + format(emoji_a + ord(country2[1]) - ord("A"), "X")
    return a + b


def create_referee(data):
    new_card = card.replace("<!--current_day-->", date)
    new_card = new_card.replace("<!--is_active-->", data['is_active'])
    new_card = new_card.replace("<!--name-->", data['name'])
    category = data['category'] if data['category'] in ["III","II","I","IS","RCM"] else "?"
    new_card = new_card.replace("<!--category-->", category)
    new_card = new_card.replace("<!--photo-->", data['photo'])
    new_card = new_card.replace("<!--birthdate-->", data['birthdate'])
    new_card = new_card.replace("<!--country-->", data['country'])
    sex = "♀" if data['sex'] == "F" else "♂" if data['sex'] == "M" else "?"
    new_card = new_card.replace("<!--sex-->", sex)
    country2 = cc.convert(names = data['country'][:3], src='IOC', to='ISO2')
    emoji_flag = get_emoji_flag(country2)
    new_card = new_card.replace("<!--emoji_flag-->", emoji_flag)
    new_page = page.replace("<!--new_info-->", new_card)
    new_page = new_page.replace("<!--id_number-->", data['id_number'])
    with open(f"{base_path}/{int(data['id_number']):07d}.html", "w") as f:
        f.write(new_page)


def change_referee(current, changes):
    filename = [filename for filename in os.listdir(f'{base_path}') if changes['key'] in filename][0]
    with open(f"{base_path}/{filename}") as f:
        page = f.read()
    page = page.replace(history_header, "")

    data = current[changes['key']]
    
    new_card = card.replace("<!--current_day-->", date)
    new_card = new_card.replace("<!--is_active-->", data['is_active'])
    category = data['category'] if data['category'] in ["III","II","I","IS","RCM"] else "?"
    new_card = new_card.replace("<!--category-->", category)
    new_card = new_card.replace("<!--photo-->", data['photo'])
    new_card = new_card.replace("<!--birthdate-->", data['birthdate'])
    new_card = new_card.replace("<!--country-->", data['country'])
    sex = "♀" if data['sex'] == "F" else "♂" if data['sex'] == "M" else "?"
    new_card = new_card.replace("<!--sex-->", sex)
    country2 = cc.convert(names = data['country'][:3], src='IOC', to='ISO2')
    emoji_flag = get_emoji_flag(country2)
    new_card = new_card.replace("<!--emoji_flag-->", emoji_flag)
    new_card = new_card.replace("<!--id_number-->", data['id_number'])
    new_card = new_card.replace("<!--name-->", data['name'])
    data_changed = list(changes['changes'].keys())
    if "category" in data_changed:
        new_card = new_card.replace("blink_me__category", "blink_me__")
    if "photo" in data_changed:
        new_card = new_card.replace("blink_me__photo", "blink_me__")
    if "name" in data_changed:
        new_card = new_card.replace("blink_me__name", "blink_me__")
    if "country" in data_changed:
        new_card = new_card.replace("blink_me__country", "blink_me__")
    if "sex" in data_changed or "birthdate" in data_changed:
        new_card = new_card.replace("blink_me__other", "blink_me__")
    new_page = page.replace("<!--new_info-->\n", new_card)
    with open(f"{base_path}/{int(data['id_number']):07d}.html", "w") as f:
        f.write(new_page)


def remove_referee(data):
    filename = [filename for filename in os.listdir('{base_path}') if data['id_number'] in filename][0]
    with open(f"{base_path}/{filename}") as f:
        page = f.read()
    page = page.replace(history_header, "")
    
    new_card = card.replace("<!--current_day-->", date)
    new_card = new_card.replace("<!--is_active-->", "null")
    category = data['category'] if data['category'] in ["III","II","I","IS","RCM"] else "?"
    new_card = new_card.replace("<!--category-->", category)
    new_card = new_card.replace("<!--photo-->", data['photo'])
    new_card = new_card.replace("<!--birthdate-->", data['birthdate'])
    new_card = new_card.replace("<!--country-->", data['country'])
    sex = "♀" if data['sex'] == "F" else "♂" if data['sex'] == "M" else "?"
    new_card = new_card.replace("<!--sex-->", sex)
    country2 = cc.convert(names = data['country'][:3], src='IOC', to='ISO2')
    emoji_flag = get_emoji_flag(country2)
    new_card = new_card.replace("<!--emoji_flag-->", emoji_flag)
    new_card = new_card.replace("<!--id_number-->", data['id_number'])
    new_card = new_card.replace("<!--name-->", data['name'])

    new_page = page.replace("<!--new_info-->\n", new_card)
    with open(f"{base_path}/{int(data['id_number']):07d}.html", "w") as f:
        f.write(new_page)


def main():
    old = load_csv(open("last"), key="id_number")
    current = load_csv(open("uww_referees.csv"), key="id_number")
    diff = compare(old, current)
    
    for changes in tqdm(diff['changed']):
        change_referee(current, changes)
    for new_ref in tqdm(diff['added']):
        create_referee(new_ref)
    for old_ref in tqdm(diff['removed']):
        remove_referee(old_ref)

    sys.stdout = open('referee_changes.html','wt')
    print("""<!doctype html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, height=device-height, initial-scale=1.0"/>
        <title>Referee Changes</title>
        <meta name="description" content="rgfm's UWW Tools"/>
        <link rel="canonical" href="https://uww.rgfm.ch/"/i>
        <style>
            body {margin: 5% auto; background: #ffffff; color: #000000; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 16px; line-height: 1.8; text-shadow: 0 1px 0 #ffffff; max-width: 73%;}
            code {background: white;}
            a {border-bottom: 1px solid #444444; color: #444444; text-decoration: none;}
            a:hover {border-bottom: 0;}
            img {width: 80%; height: auto;}
            form  { display: table;      }
            p     { display: table-row;  }
            label { display: table-cell; }
            input { display: table-cell; }
        </style>
    </head>
    <body>
        <header>""")
    print(f"<h1>Referee Updates, {date}</h1>")
    print("</header>")
    if diff['changed']:
        print("<ul>")
        for changes in diff['changed']:
            print("<li>")
            id = int(changes["key"])
            print(f'<a href="referees/{id:07d}.html">Referee {id} ({current[str(id)]["name"]} - {current[str(id)]["country"]})</a> has changed:')
            print("<ul>")
            for col, from_to in changes['changes'].items():
                if col == 'photo':
                    print(f"<li>The profile picture</li>")
                else:
                    print(f"<li>{col.title().replace('_', ' ')} from {from_to[0]} to {from_to[1]}</li>")
            print("</ul>")
            print("</li>")
        print("</ul>")
    
    if diff['added']:
        print("<h2>New Referees</h2>")
        print("<ul>")
        for new_ref in diff['added']:
            id = int(new_ref["id_number"])
            print(f'<li><a href="referees/{id:07d}.html">Referee {id} ({new_ref["name"]} - {new_ref["country"]})</a></li>')
        print("</ul>")
    
    if diff['removed']:
        print("<h2>Retired Referees</h2>")
        print("<ul>")
        for old_ref in diff['removed']:
            id = int(old_ref["id_number"])
            print(f'<li><a href="referees/{id:07d}.html">Referee {id} ({old_ref["name"]} - {old_ref["country"]})</a></li>')
        print("</ul>")
    print("</body>")
    print("</html>")


if __name__ == '__main__':
    sys.exit(main())
