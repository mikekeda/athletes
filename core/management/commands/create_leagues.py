import logging
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from django.core.management import BaseCommand

from core.models import Team, League


log = logging.getLogger('athletes')


class Command(BaseCommand):
    # Show this when the user types help
    help = "Create leagues from teams"

    def handle(self, *args, **options):
        self.stdout.write("Started creating leagues")

        tids = list(Team.objects.values_list('id', flat=True))

        self.stdout.write(f"{len(tids)} teams to parse leagues")

        for i, tid in enumerate(tids):
            team = Team.objects.get(id=tid)

            if not team.additional_info.get('League'):
                continue

            self.stdout.write(f"{i}: check {team.name} team")

            site = urlparse(team.wiki)
            site = f'{site.scheme}://{site.hostname}'
            html = requests.get(team.wiki)
            soup = BeautifulSoup(html.content, 'html.parser')
            card = soup.find("table", {"class": "vcard"})

            if not card:
                continue

            for row in card.select('tr'):
                td = row.find_all(recursive=False)
                if td:
                    key = str(td[0].string or td[0].text).replace('\xa0', ' ')

                    if key == 'League' and td[1]:
                        link = td[1].find('a')
                        if not link or not link.get('href'):
                            continue

                        if link['href'][:4] != 'http':
                            link['href'] = site + link['href']

                        league, created = League.objects.get_or_create(
                            wiki=link['href'],
                            location_market=team.location_market,
                            gender=team.gender,
                            category=team.category
                        )
                        if created:
                            self.stdout.write(f"{league.name} created")
