import country_converter as coco

import glob
import json
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
possible_categories = ["III","II","I","IS","IS-RCM","INS","RCM","RAB","HON"]

BLINK_CLASS = "blink_off"
ID_CARD_PATH = "res/id_card.html"
REF_PAGE_PATH = "res/referee_page.html"
CHANGELOG_PATH = "res/referee_changes.html"

def format_date(date_string: str) -> str:
    new_date = datetime.strptime(date_string, "%Y-%m-%d")
    return new_date.strftime("%-d %b %Y")


def get_emoji_letter_flag(letter: str) -> str:
    hexValue = format(emoji_a + ord(letter) - ord("A"), "X")
    return chr(int(hexValue, 16))


def get_emoji_flag(country2: str) -> str:
    return get_emoji_letter_flag(country2[0]) + get_emoji_letter_flag(country2[1])


def get_ref_path_folder(id_number: str) -> str:
    return f"{base_path}/{int(id_number)}"


def get_ref_path(id_number: str) -> str:
    return f"{get_ref_path_folder(id_number)}/index.html"


def get_change_reason(data: dict, changes: dict) -> str:
    if "category" in changes:
        change = changes['category']
        if change[0] == 'RCM':
            return "Category updated on"
        if change[1] not in possible_categories:
            return "Category erased on"
        if change[0] not in possible_categories:
            return "Category readded on"
        if possible_categories.index(change[0]) <= possible_categories.index(change[1]):
            return "Category upgraded on"
        return "Category downgraded on"
    if "name" in changes:
        return "Name changed on"
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
        return "Active as of" if "True" == data['is_active'] else "Inactive as of"
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
    with open(ID_CARD_PATH) as f:
        card = BeautifulSoup(f.read(), 'html.parser')

    referee_id = data['id_number']
    country_name = data['country'][:3]
    if country_name == 'PYF':
        emoji_flag = "🇵🇫"
    else:
        country2 = cc.convert(names = country_name, src='IOC', to='ISO2')
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
    path = REF_PAGE_PATH
    if already_exists:
        path = get_ref_path(id_number)
    with open(path) as f:
        page = BeautifulSoup(f.read(), 'html.parser')

    page.find(id="pageTitle").string = f"Referee #{id_number}"
    currentState = page.find(id="currentState").find("div")
    if currentState:
        page.find(id="historyContent").insert_after(currentState)
    page.find(id="currentState").append(card.extract())

    if not os.path.isdir(get_ref_path_folder(id_number)):
        os.makedirs(get_ref_path_folder(id_number))

    with open(get_ref_path(id_number), "w") as f:
        f.write(str(page))


def create_referee(data: dict, already_exists: bool, reason="Created on") -> None:
    update_referee(update_card(data, reason), already_exists, data['id_number'])


def change_referee(current: dict, changes: dict) -> None:
    data = current[changes['key']]
    card = update_card(data, get_change_reason(data, changes['changes']))
    
    for item_changed in list(changes['changes'].keys()):
        if "is_active" not in item_changed and 'athena' not in item_changed:
            elementChanged = card.find(id=f"user{item_changed.title()}_{date}")
            elementChanged['class'] = [BLINK_CLASS, item_changed]

    update_referee(card, True, changes["key"])


def remove_referee(data: dict) -> None:
    update_referee(update_card(data, "Retired as of", True), True, data["id_number"])


def list_changes(doc: BeautifulSoup, data: dict, diff: dict, key: str, sublist: bool) -> None:
    if diff[key]:
        title = doc.new_tag("h2")

        titles = {
            'changed': 'Changes',
            'added': 'New Referees',
            'removed': 'Retired Referees',
        }
        
        title.string = f"{titles[key]} ({len(diff[key])})"
        doc.find(id=key).insert_after(title)

        added_list = doc.new_tag("ul")
        title.insert_after(added_list)

        for ref in diff[key]:
            item = doc.new_tag("li")
            added_list.append(item)

            if sublist:
                id = int(ref["key"])
                ind_data = data[str(id)]
            else:
                id = int(ref["id_number"])
                ind_data = ref
                
            name = ind_data["name"]
            country = ind_data["country"]
            category = ind_data["category"]
            if not category:
                category = '?'
            birthdate = ind_data["birthdate"]
            age = int(date.split('-')[0]) - int(birthdate.split('-')[0])

            link = doc.new_tag("a", href=f"/{get_ref_path_folder(id)}")
            link.string = f"{name} ({country}, {category}, {age} years old this year)"
            item.append(link)

            if sublist:
                inside_list = doc.new_tag("ul")
                item.append(inside_list)
    
                for col, from_to in ref['changes'].items():
                    inside_item = doc.new_tag("li")
                    inside_list.append(inside_item)
                    if col == 'photo':
                        inside_item.string = "The profile picture has changed."
                    elif col == 'is_active':
                        if from_to[1] == 'True':
                            inside_item.string = "Licence is now active."
                        else:
                            inside_item.string = "Licence has been deactivated."
                    else:
                        fromStr = from_to[0] if from_to[0] else "?"
                        toStr = from_to[1] if from_to[1] else "?"
                        title = col.title().replace('_', ' ')
                        title = 'Gender' if title == 'Sex' else title
                        inside_item.string = f"{title} from {fromStr} to {toStr}"
        

def updateIndex(current: dict) -> None:
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


def saveChangelog(data: dict, diff: dict) -> None:
    with open(CHANGELOG_PATH) as f:
        changelog = BeautifulSoup(f.read(), 'html.parser')

    title = "Referee Updates"
    changelog.find("title").string = f"{title} - {date}"
    changelog.find(id="title").string = f"{title}, {format_date(date)}"

    list_changes(changelog, data, diff, 'changed', True)
    list_changes(changelog, data, diff, 'added', False)
    list_changes(changelog, data, diff, 'removed', False)

    with open("index.html", "w") as f:
        f.write(str(changelog))


def main() -> None:
    old = load_csv(open("last.csv"), key="id_number")
    current = load_csv(open("uww_referees.csv"), key="id_number")
    diff = compare(old, current)
    
    updateIndex(current)

    for changes in diff['changed']:
        change_referee(current, changes)
    for new_ref in diff['added']:
        already_exists = os.path.isfile(get_ref_path(new_ref['id_number']))
        create_referee(new_ref, already_exists)
    for old_ref in diff['removed']:
        remove_referee(old_ref)

    saveChangelog(current, diff)


if __name__ == '__main__':
    sys.exit(main())
