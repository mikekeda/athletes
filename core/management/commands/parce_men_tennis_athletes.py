import datetime

import requests
from bs4 import BeautifulSoup
from django.core.management import BaseCommand

from core.constans import COUNTRy_CODE3_TO_CODE2
from core.models import Athlete


class Command(BaseCommand):
    # Show this when the user types help
    help = "Parse Tennis players."

    def handle(self, *args, **options):
        self.stdout.write("Started parsing Tennis players")

        urls = [
            "https://www.atpworldtour.com/en/players/radu-albot/a829/overview"
        ]

        for url in urls:
            html = requests.get(url)
            soup = BeautifulSoup(html.content, 'html.parser')
            card = soup.select_one('.player-profile-hero-overflow')
            first_name = card.select_one('.first-name').string
            last_name = card.select_one('.last-name').string
            name = f'{first_name} {last_name}'

            self.stdout.write(f"Parsing {name}")

            wiki_url = (
                "https://en.wikipedia.org/w/api.php?action=opensearch"
                f"&search={name}"
            )
            res = requests.get(wiki_url)
            if res.status_code == 200:
                data = res.json()
                wiki = data[3][0]

                # If we have many links - try to get a link with word "tennis".
                data[3] = [link for link in data[3] if 'tennis' in link]
                if data[3]:
                    wiki = data[3][0]
            else:
                self.stdout.write("Failed getting wiki info for {name}")
                continue

            athlete, _ = Athlete.objects.get_or_create(wiki=wiki)
            athlete.get_data_from_wiki()

            athlete.category = "Tennis"
            athlete.gender = "male"
            athlete.additional_info['Data source'] = url

            country_code = card.select_one('.player-flag-code').string
            athlete.location_market = COUNTRy_CODE3_TO_CODE2[country_code]

            birthday = card.select_one('.table-birthday').string
            birthday = birthday.strip().strip('(').strip(')')
            athlete.birthday = datetime.datetime.strptime(birthday, "%Y.%m.%d")

            athlete.save()
