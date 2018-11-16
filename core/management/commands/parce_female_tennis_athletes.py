import datetime
import logging

import requests
from bs4 import BeautifulSoup
from django.core.management import BaseCommand

from core.constans import COUNTRIES, COUNTRY_CODE3_TO_CODE2
from core.models import Athlete

log = logging.getLogger('athletes')


def _parse_tennis(url: str, info: dict):
    html = requests.get(url)
    soup = BeautifulSoup(html.content, 'html.parser')
    card = soup.select_one('.node.node--players.view-mode-highlight_player')
    first_name = card.select_one('.field--name-field-firstname').string
    last_name = card.select_one('.field--name-field-lastname').string
    name = f'{first_name} {last_name}'

    log.info(f"Parsing {name} ({url})")

    wiki_url = (
        "https://en.wikipedia.org/w/api.php?action=opensearch"
        f"&search={name}"
    )
    res = requests.get(wiki_url)
    if res.status_code == 200:
        data = res.json()

        if not data[3]:
            log.warning(f"Failed getting wiki page for {name}")
            return

        wiki = data[3][0]

        # If we have many links - try to get a link with word "tennis".
        data[3] = [link for link in data[3] if 'tennis' in link]
        if data[3]:
            wiki = data[3][0]

        birthday = card.select_one(
            '.field--name-field-date-of-birth .date-display-single'
        )

        if birthday and birthday.string:
            birthday = birthday['content'][:10]
            birthday = datetime.datetime.strptime(birthday, "%Y-%m-%d")
            defaults = {'birthday': birthday}
        else:
            defaults = {}

        try:
            athlete, _ = Athlete.objects.get_or_create(
                wiki=wiki,
                defaults=defaults
            )
        except ValueError:
            log.warning(f"Failed to parse wiki info for {name}")
            return

        athlete.name = name

        athlete.category = "Tennis"
        athlete.gender = "female"
        athlete.additional_info['Data source'] = url

        location_market = card.select_one(
            ".field--name-field-residence"
        )
        if location_market and location_market.string:
            location_market = location_market.string.strip()
            geo_data = athlete.geocode(location_market)
            if geo_data['results']:
                for component in geo_data['results'][0]['address_components']:
                    if 'country' in component['types'] and \
                            component['short_name'] in COUNTRIES:
                        athlete.location_market = component['short_name']

        country_code = card.select_one(
            '.field--name-field-country-code'
        ).string
        athlete.domestic_market = COUNTRY_CODE3_TO_CODE2[country_code]

        if birthday:
            athlete.birthday = birthday

        athlete.additional_info['Singles ranking'] = card.select_one(
            '.field--name-field-singles-ranking'
        ).string.strip()

        athlete.additional_info['Doubles ranking'] = card.select_one(
            '.field--name-field-doubles-ranking'
        ).string.strip()

        if info.get('tourn'):
            athlete.additional_info['tourn'] = info.get('tourn')

        if info.get('points'):
            athlete.additional_info['points'] = info.get('points')

        athlete.save()
    else:
        log.warning(f"Failed getting wiki info for {name}")


class Command(BaseCommand):
    # Show this when the user types help
    help = "Parse Tennis players."

    def handle(self, *args, **options):
        self.stdout.write("Started parsing Tennis players")

        site = "http://www.wtatennis.com"
        url = f"{site}/node/239683/singles/ranking.json"
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()

            for item in data:
                link = BeautifulSoup(item['fullname'],
                                     'html.parser').select_one('a')

                if not Athlete.objects.filter(
                        name__icontains=link.string).exists():
                    _parse_tennis(site + link['href'], item)
                else:
                    log.info(f"Skip {link.string}")

        self.stdout.write("Finished parsing Tennis players")
