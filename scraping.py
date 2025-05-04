import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

years = list(range(2025, 2024, -1))
all_matches = []
standings_url = "https://fbref.com/en/comps/9/Premier-League-Stats"

for year in years:
    data = requests.get(standings_url)
    time.sleep(5)
    soup = BeautifulSoup(data.text)
    standings_table = soup.select('table.stats_table')[0]

    links = [l.get("href") for l in standings_table.find_all('a')]
    links = [l for l in links if '/squads/' in l]
    team_urls = [f"https://fbref.com{l}" for l in links]

    previous_season = soup.select("a.prev")[0].get("href")
    standings_url = f"https://fbref.com{previous_season}"

    for team_url in team_urls:
        team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")

        data = requests.get(team_url)
        matches = pd.read_html(data.text, match="Scores & Fixtures")[0]

        soup = BeautifulSoup(data.text)
        linksa = [l.get('href') for l in soup.find_all('a')]
        linksShooting = [l for l in linksa if l and 'all_comps/shooting/' in l]
        dataShooting = requests.get(f"https://fbref.com{linksShooting[0]}")
        print(f"https://fbref.com{linksShooting[0]}")
        shooting = pd.read_html(dataShooting.text, match="Shooting")[0]
        shooting.columns = shooting.columns.droplevel()

        linksGCA = [l for l in linksa if l and 'all_comps/gca/' in l]
        dataGCA = requests.get(f"https://fbref.com{linksGCA[0]}")
        gca = pd.read_html(dataGCA.text, match="Goal and Shot Creation")[0]
        gca.columns = gca.columns.droplevel()
        gca = gca.loc[:, ~gca.columns.duplicated()]
        gca = gca[["Date","SCA","PassLive","PassDead","TO","Fld","Def"]]

        try:
            team_data = matches.merge(shooting[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]], on="Date")
        except ValueError:
            continue

        try:
            team_data = team_data.merge(gca[["Date", "SCA", "PassLive", "PassDead", "TO", "Fld", "Def"]], on="Date")
        except ValueError:
            continue

        team_data = team_data[team_data["Comp"] == "Premier League"]
        team_data["Season"] = year
        team_data["Team"] = team_name
        all_matches.append(team_data)
        time.sleep(20)

match_df = pd.concat(all_matches)

match_df.columns = [c.lower() for c in match_df.columns]

match_df.to_csv("matches.csv")

        
