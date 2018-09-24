from bs4 import BeautifulSoup
import logging
import requests
from urllib.parse import urlparse

from django.db.utils import IntegrityError

from core.celery import app
from core.constans import COUNTRIES
from core.models import Athlete, Team


log = logging.getLogger('athletes')


def validate_link_and_create_athlete(link, site, data):
    """ Validate the link and create an athlete. """
    # If link has a space - it's player name.
    if link and link.string and len(link.string.split()) > 1:
        if link['href'][:4] != 'http':
            full_link = site + link['href']
        else:
            full_link = link['href']
        # Asynchronously add an athlete.
        if create_athlete_task(full_link, data):
            return full_link, True
        else:
            return full_link, False

    return None, False


def create_athlete_task(wiki, data):
    """ Task to crawl athletes from wiki team page. """
    athlete = Athlete.objects.filter(wiki=wiki).first()
    data = {key: val for key, val in data.items() if val}  # remove empty vals

    try:
        if not athlete:
            # Create an athlete.
            Athlete.objects.create(wiki=wiki, **data)
        else:
            # Update an athlete.
            for field in data:
                if not getattr(athlete, field):
                    setattr(athlete, field, data[field])
            athlete.save()
        return True
    except IntegrityError as e:
        log.warning(f"{repr(e)}: Skip athlete for {wiki}")
        return False


@app.task
def parse_team(cleaned_data, skip_errors=False):
    wiki_url = cleaned_data.get('wiki', '')
    log.info(f"parsing team {wiki_url}")
    site = urlparse(wiki_url)
    site = f'{site.scheme}://{site.hostname}'
    html = requests.get(wiki_url)
    soup = BeautifulSoup(html.content, 'html.parser')
    title = soup.select(
        "#Current_squad") or soup.select(
        "#Current_roster") or soup.select(
        "#Roster") or soup.select(
        "#First-team_squad") or soup.select(
        "#First_team_squad") or soup.select(
        "#Team_squad") or soup.select(
        "#Squad") or soup.select(
        "#Players") or soup.select(
        "#Current_Squad") or soup.select(
        "#Current_roster_and_coaching_staff") or soup.select(
        "#First_Team_Squad") or soup.select(
        "#Current_squad[11]") or soup.select(
        "#Current_players") or soup.select(
        "#Current_first_team_squad") or soup.select(
        "#Current_roster_and_Baseball_Hall_of_Fame") or soup.select(
        "#Team_roster") or soup.select(
        "#Team_roster_2018") or soup.select(
        "#2018_squad") or soup.select(
        "#Current_playing_squad") or soup.select(
        "#Playing_squad") or soup.select(
        "#Current_playing_list_and_coaches") or soup.select(
        "#Current_playing_lists")
    if skip_errors and not title:
        return
    cleaned_data['name'] = soup.title.string.split(' - Wikipedia')[0]
    table = title[0].parent.find_next_sibling("table")

    team, _ = Team.objects.get_or_create(**cleaned_data)
    team.get_data_from_wiki(soup)
    team.save()

    cleaned_data['team'] = cleaned_data.pop('name', '')
    cleaned_data['team_model'] = team
    cleaned_data.pop('wiki', '')
    result = {'skipped': [], 'parsed': []}

    if cleaned_data.get('category') in ("American Football", "Baseball"):
        links = table.select("td > ul > li > a")

        for link in links:
            full_link, status = validate_link_and_create_athlete(
                link, site, cleaned_data
            )
            result[['skipped', 'parsed'][status]].append(full_link)
    elif cleaned_data.get('category') == "Ice Hockey":
        links = table.select("tr > td span.vcard a")

        for link in links:
            full_link, status = validate_link_and_create_athlete(
                link, site, cleaned_data
            )
            result[['skipped', 'parsed'][status]].append(full_link)
    elif cleaned_data.get('category') == "Cycling":
        links = table.select("tr > td span a")

        for link in links:
            full_link, status = validate_link_and_create_athlete(
                link, site, cleaned_data
            )
            result[['skipped', 'parsed'][status]].append(full_link)
    elif cleaned_data.get('category') == "Rugby":
        links = table.select(
            "tr > td span.fn > a") or table.select(
            "tr > td ul > li a")

        for link in links:
            full_link, status = validate_link_and_create_athlete(
                link, site, cleaned_data
            )
            result[['skipped', 'parsed'][status]].append(full_link)
    elif cleaned_data.get('category') == "Australian Football":
        links = table.select("td > ul > li  a")

        for link in links:
            full_link, status = validate_link_and_create_athlete(
                link, site, cleaned_data
            )
            result[['skipped', 'parsed'][status]].append(full_link)
    elif cleaned_data.get('category') == "Cricket":
        links = table.select("tr > td:nth-of-type(2) > a")

        for link in links:
            full_link, status = validate_link_and_create_athlete(
                link, site, cleaned_data
            )
            result[['skipped', 'parsed'][status]].append(full_link)
    else:
        # Default parsing.
        # Go through all table rows.
        for row in table.find_all("tr"):
            td = row.find_all(recursive=False)
            if len(td) > 3:
                for i in (2, 3):  # try to find players in 2th or 3th
                    link = td[i].find("a", recursive=False)
                    if not link:
                        # Sometimes a is wrapped with span.
                        link = td[i].find("span", recursive=False)
                        if link:
                            link = link.find("a", recursive=False)

                    if not link:
                        link = td[i].select_one("span.vcard a")

                    if link and link.string in [
                        "United States", "South Korea", "North Korea",
                        "Ivory Coast"
                    ] + list(COUNTRIES.values()):
                        continue  # it's not a athlete

                    full_link, status = validate_link_and_create_athlete(
                        link, site, cleaned_data
                    )
                    result[['skipped', 'parsed'][status]].append(
                        full_link)

    result['skipped'] = [link for link in result['skipped'] if link]

    return result
