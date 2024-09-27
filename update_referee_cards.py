import country_converter as coco

import glob
import os
import sys

from bs4 import BeautifulSoup
from csv_diff import load_csv, compare
from datetime import datetime
from tqdm import tqdm


cc = coco.CountryConverter()
emoji_a = 127462
base_path = "referees"
date = datetime.today().strftime('%Y-%m-%d')
possible_categories = ["III","II","I","IS","RCM"]
BLINK_CLASS = "blink_off"

def format_date(date_string: str) -> str:
    new_date = datetime.strptime(date_string, "%Y-%m-%d")
    return new_date.strftime("%-d %b %Y")


def get_emoji_letter_flag(letter: str) -> str:
    hexValue = format(emoji_a + ord(letter) - ord("A"), "X")
    return chr(int(hexValue, 16))


def get_emoji_flag(country2: str) -> str:
    return get_emoji_letter_flag(country2[0]) + get_emoji_letter_flag(country2[1])


def get_ref_path(id_number: str) -> str:
    return f"{base_path}/{int(id_number):07d}.html"


def get_change_reason(data: dict, changes: dict) -> str:
    if "category" in changes:
        change = changes['category']
        if change[1] not in possible_categories:
            return "Category erased on"
        if change[0] not in possible_categories:
            return "Category readded on"
        if possible_categories.index(change[0]) <= possible_categories.index(change[1]):
            return "Category upgraded on"
        else:
            return "Category downgraded on"
    if "name" in changes:
        return "Named changed on"
    if "sex" in changes:
        return "Gender changed on"
    if "country" in changes:
        return "Country changed on"
    if "birthdate" in changes:
        return "Birthdate changed on"
    if "photo" in changes:
        return "Photo changed on"
    if "new_is_active" in changes:
        return "Activity checked on"
    if "is_active" in changes:
        return "Active as of" if data['is_active'] else "Inactive as of"
    return "Effective from"


def setValues(doc: BeautifulSoup, id: str, newValues: list[str], attributes: list[str]) -> None:
    node = doc.find(id=id)
    for newValue, attribute in zip(newValues, attributes):
        if attribute == 'text':
            node.string = newValue
        else:
            node[attribute] = newValue
    node['id'] = f"{id}_{date}"


def setValue(doc: BeautifulSoup, id: str, newValue: str, attribute='text') -> None:
    setValues(doc, id, [newValue], [attribute])


def update_card(data: dict, reason: str, is_removed=False) -> BeautifulSoup:
    with open("uww_card.html") as f:
        card = BeautifulSoup(f.read(), 'html.parser')

    referee_id = data['id_number']
    country2 = cc.convert(names = data['country'][:3], src='IOC', to='ISO2')
    emoji_flag = get_emoji_flag(country2)
    sex = "♀" if data['sex'] == "F" else "♂" if data['sex'] == "M" else "♂♀"
    category = data['category'] if data['category'] in possible_categories else "?"

    setValues(card, 'state', [], [])
    setValue(card, 'stateTitle', f"{reason} {format_date(date)}")
    setValue(card, 'userAthena', data['athena'], 'href')
    setValues(card, 'userPhoto', [data['photo'], f"Photo of referee {data['name']}"], ['src', 'alt'])
    if 'is_active' in data or is_removed:
        activity = data['is_active'] if not is_removed else 'over'
    else:
        activity = 'unknown'
    setValue(card, 'right', f"insideColumn right activity{activity.title()}", 'class')
    setValue(card, 'userName', data['name'])
    setValue(card, 'userCountry', f"{data['country']} {emoji_flag}")
    setValues(card, 'userBirthdate', [format_date(data['birthdate']), data['birthdate']], ['text', 'iso'])
    setValue(card, 'userSex', sex)
    setValue(card, 'userCategory', f"Category {category}")
    
    return card


def update_referee(card: BeautifulSoup, already_exists: bool, id_number: str) -> None:
    path = "uww_referee.html"
    if already_exists:
        path = get_ref_path(id_number)
    with open(path) as f:
        page = BeautifulSoup(f.read(), 'html.parser')

    page.find(id="pageTitle").string = f"Referee #{id_number}"
    currentState = page.find(id="currentState").find("div")
    if currentState:
        page.find(id="historyContent").insert_after(currentState)
    page.find(id="currentState").append(card.extract())

    with open(get_ref_path(id_number), "w") as f:
        f.write(str(page))


def create_referee(data: dict, already_exists: bool, reason="Created on") -> None:
    update_referee(update_card(data, reason), False, data['id_number'])


def change_referee(current: dict, changes: dict) -> None:
    data = current[changes['key']]
    card = update_card(data, get_change_reason(data, changes['changes']))
    
    for item_changed in list(changes['changes'].keys()):
        if not "is_active" in item_changed:
            elementChanged = card.find(id=f"user{item_changed.title()}_{date}")
            elementChanged['class'] = [BLINK_CLASS, item_changed]

    update_referee(card, True, changes["key"])


def remove_referee(data: dict) -> None:
    update_referee(update_card(data, "Retired as of", True), True, data["id_number"])


def main() -> None:
    old = load_csv(open("last"), key="id_number")
    current = load_csv(open("uww_referees.csv"), key="id_number")
    diff = compare(old, current)
    
    for changes in diff['changed']:
        if changes['changes'] != 1 and not 'athena' in changes['changes']:
            change_referee(current, changes)
    for new_ref in diff['added']:
        already_exists = os.path.isfile(get_ref_path(new_ref['id_number']))
        create_referee(new_ref, already_exists)
    for old_ref in diff['removed']:
        remove_referee(old_ref)
    if diff['columns_added']:
        for key in current.keys():
            change_referee(current, {'key': key, 'changes': {'new_is_active': ''}})

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
            print(f'<a href="{get_ref_path(id)}">Referee {id} ({current[str(id)]["name"]} - {current[str(id)]["country"]})</a> has changed:')
            print("<ul>")
            for col, from_to in changes['changes'].items():
                if col == 'photo':
                    print(f"<li>The profile picture</li>")
                elif col == 'is_active':
                    if from_to[1]:
                        print("<li>Licence is now active.</li>")
                    else:
                        print("<li>Licence has been deactivated.</li>")
                else:
                    fromStr = from_to[0] if from_to[0] else "?"
                    print(f"<li>{col.title().replace('_', ' ')} from {fromStr} to {from_to[1]}</li>")
            print("</ul>")
            print("</li>")
        print("</ul>")
    
    if diff['added']:
        print("<h2>New Referees</h2>")
        print("<ul>")
        for new_ref in diff['added']:
            id = int(new_ref["id_number"])
            print(f'<li><a href="{get_ref_path(id)}">Referee {id} ({new_ref["name"]} - {new_ref["country"]})</a></li>')
        print("</ul>")
    
    if diff['removed']:
        print("<h2>Retired Referees</h2>")
        print("<ul>")
        for old_ref in diff['removed']:
            id = int(old_ref["id_number"])
            print(f'<li><a href="{get_ref_path(id)}">Referee {id} ({old_ref["name"]} - {old_ref["country"]})</a></li>')
        print("</ul>")
    print("</body>")
    print("</html>")


if __name__ == '__main__':
    sys.exit(main())
