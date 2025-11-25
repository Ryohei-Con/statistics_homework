import re
import time
from pathlib import Path

import numpy as np
import requests
from bs4 import BeautifulSoup

BASE_URLS = [
    "https://www.boatrace.jp/owpc/pc/race/gradesch?year=2024&hcd=01",
    "https://www.boatrace.jp/owpc/pc/race/gradesch?year=2024&hcd=02",
    "https://www.boatrace.jp/owpc/pc/race/gradesch?year=2024&hcd=03"
]
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"}
html_root_path = Path("scraping/downloaded_html")


def get_tournament_urls(url: str):
    response = requests.get(url, headers=HEADERS)
    print(f"status code: {response.status_code}")
    soup = BeautifulSoup(response.text, "html.parser")
    main = soup.find("main")
    table = main.find("table")
    if table is None:
        print("レース結果が見つかりませんでした。")
        return None
    tbodys = table.find_all("tbody")
    race_lists = []
    race_results = []
    for tbody in tbodys:
        td_tags = tbody.find_all("td")
        race_list = td_tags[5].find("a").get("href")
        race_result = td_tags[7].find("a").get("href")
        race_list = "https://www.boatrace.jp" + race_list
        race_result = "https://www.boatrace.jp" + race_result
        race_lists.append(race_list)
        race_results.append(race_result)
    return {"tournament_lists": race_lists, "tournament_results": race_results}


def get_all_dates(url: str):
    response = requests.get(url, headers=HEADERS)
    print(f"status code: {response.status_code}")
    soup = BeautifulSoup(response.text, "html.parser")
    a_tags = soup.find_all('a', class_='tab2_inner')

    href_list = []
    for tag in a_tags:
        href = tag.get('href')
        href = "https://www.boatrace.jp" + href
        href_list.append(href)
    return href_list


def get_all_race_cards(url: str):
    """
    レース情報のページからそれぞれの出走表のリンクをとってくる
    """
    all_race_dates = get_all_dates(url)
    for url in all_race_dates:
        response = requests.get(url, headers=HEADERS)
        print(f"status code: {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")
        target_links = soup.find_all('a', string='出走表')

        href_list = []
        for tag in target_links:
            href = tag.get('href')
            href = "https://www.boatrace.jp" + href
            # hrefが存在し、かつURL構造がレース一覧(racelist)のものであるか確認
            if href and ('/race/racelist' in href):
                href_list.append(href)
    return href_list


def get_all_result_races(url: str):
    """
    レース結果のページからそれぞれのレース結果のリンクをとってくる。
    """
    all_result_dates = get_all_dates(url)
    for url in all_result_dates:
        response = requests.get(url, headers=HEADERS)
        print(f"status code: {response.status_code}")
        soup = BeautifulSoup(response.text, "html.parser")
        race_links = soup.find_all("a", string=re.compile(r"^\d+R$"))
        href_list = []

        for tag in race_links:
            href = tag.get('href')
            href = "https://www.boatrace.jp" + href
            # hrefが存在し、かつURLにレース結果(raceresult)が含まれているか確認
            if href and 'raceresult' in href:
                href_list.append(href)
        return href_list


def download_html(url, folder_name: str, file_name: str):
    html_folder = html_root_path / folder_name
    html_folder.mkdir(exist_ok=True)
    html_file = (html_folder / file_name).with_suffix(".html")
    response = requests.get(url, headers=HEADERS)
    print(f"status code: {response.status_code}")
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(response.text)


def main():
    for base_url in BASE_URLS:
        competition_urls = get_tournament_urls(base_url)
        for url_race, url_result in zip(competition_urls["tournament_lists"], competition_urls["tournament_results"]):
            url_races = get_all_race_cards(url_race)
            url_results = get_all_result_races(url_result)
            time.sleep(np.random.randint(2, 5))
            for url_race, url_result in zip(url_races, url_results):
                folder_name_race = url_race.split("?")[1]
                folder_name_result = url_race.split("?")[1]
                if folder_name_race != folder_name_result:
                    print("レースと結果が紐づきません。")
                    print(f"レースのURL: {url_race}")
                    print(f"結果のURL: {url_result}")
                    break
                # オッズのhtmlも追加で取得
                url_odds = url_race.replace("racelist", "oddstf")
                download_html(url_race, folder_name_race, "race")
                download_html(url_result, folder_name_result, "result")
                download_html(url_odds, folder_name_result, "odds")
                print(f"ダウンロードに成功しました。{folder_name_race}")


if __name__ == "__main__":
    main()
