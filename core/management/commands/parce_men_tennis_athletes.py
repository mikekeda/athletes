import datetime
import logging

import requests
from bs4 import BeautifulSoup
from django.core.management import BaseCommand

from core.constans import COUNTRIES, COUNTRY_CODE3_TO_CODE2
from core.models import Athlete

log = logging.getLogger('athletes')


def _parse_tennis(url: str):
    html = requests.get(url)
    soup = BeautifulSoup(html.content, 'html.parser')
    card = soup.select_one('.player-profile-hero-overflow')
    first_name = card.select_one('.first-name').string
    last_name = card.select_one('.last-name').string
    name = f'{first_name} {last_name}'

    log.info("Parsing %s (%s)", name, url)

    wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={name}"
    res = requests.get(wiki_url)
    if res.status_code == 200:
        data = res.json()

        if not data[3]:
            log.warning("Failed getting wiki page for %s", name)
            return None

        wiki = data[3][0]

        # If we have many links - try to get a link with word "tennis".
        data[3] = [link for link in data[3] if 'tennis' in link]
        if data[3]:
            wiki = data[3][0]

        market_row = card.select_one(
            ".player-profile-hero-table table tr:nth-of-type(2)"
        )

        birthday = card.select_one('.table-birthday')

        if birthday and birthday.string:
            birthday = birthday.string.strip().strip('(').strip(')')
            birthday = datetime.datetime.strptime(birthday, "%Y.%m.%d")
            defaults = {'birthday': birthday}
        else:
            defaults = {}

        try:
            athlete, created = Athlete.objects.get_or_create(
                wiki=wiki,
                defaults=defaults
            )
            if not created:
                log.warning("Skip athlete %s with wiki %s (already exists)", name, wiki)
                return None
        except ValueError:
            log.warning("Failed to parse wiki info for %s", name)
            return None

        athlete.name = name

        athlete.category = "Tennis"
        athlete.gender = "male"
        athlete.additional_info['Data source'] = url

        location_market = market_row.select_one(
            "td:nth-of-type(2) div:nth-of-type(3)"
        )
        if location_market and location_market.string:
            location_market = location_market.string.strip()
            geo_data = athlete.geocode(location_market)
            if geo_data['results']:
                for component in geo_data['results'][0]['address_components']:
                    if 'country' in component['types'] and \
                            component['short_name'] in COUNTRIES:
                        athlete.location_market = component['short_name']

        country_code = card.select_one('.player-flag-code').string
        athlete.domestic_market = COUNTRY_CODE3_TO_CODE2[country_code]

        if birthday:
            athlete.birthday = birthday

        athlete.additional_info['ranking'] = card.select_one(
            '.player-ranking-position .data-number'
        ).string.strip()

        athlete.save()
    else:
        log.warning("Failed getting wiki info for %s", name)

    return None


class Command(BaseCommand):
    # Show this when the user types help
    help = "Parse male Tennis players."

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('doubles', nargs='?', type=str)

    def handle(self, *args, **options):
        self.stdout.write("Started parsing Tennis players")

        start = 0
        site = "https://www.atpworldtour.com"

        while True:
            end = start + 100
            self.stdout.write(f"Parsing Tennis players ({start}-{end})")

            rankings_type = 'doubles' if options['doubles'] else 'singles'

            url = f"{site}/en/rankings/{rankings_type}/?rankRange={start}-{end}"

            html = requests.get(url)
            soup = BeautifulSoup(html.content, 'html.parser')
            links = soup.select('.player-cell > a')

            if links:
                for link in links:
                    if not Athlete.objects.filter(
                            name__icontains=link.string).exists():
                        _parse_tennis(site + link['href'])
                    else:
                        log.info("Skip %s", link.string)
            else:
                break

            start += 100

        self.stdout.write("Finished parsing Tennis players")
