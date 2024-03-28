import os
import re
import time
import pandas as pd
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime

# 상수 정의
WAIT_TIME = 1
TODAY_DATE = datetime.today().strftime('%Y%m%d')
MUSIC_COLUMNS = ['제목', '아티스트', '앨범']
PLAYLIST_URL = 'https://www.melon.com/mymusic/playlist/mymusicplaylist_list.htm'
MUSIC_URL = 'https://www.melon.com/mymusic/playlist/mymusicplaylistview_inform.htm'
EXCEL_PATH = "excel"


# 플레이리스트 키 가져오기
def get_playlist_seqs(driver, playlist_total_count):
    playlist_seqs = []
    for offset in range(1, playlist_total_count + 1, 20):
        driver.execute_script("javascript:pageObj.sendPage('" + str(offset) + "')")
        time.sleep(WAIT_TIME)

        playlist_links = driver.find_elements(By.CSS_SELECTOR, 'dt a')
        for link in playlist_links:
            playlist_seq = re.findall(r'\d+', link.get_attribute('href'))[1]
            playlist_seqs.append(playlist_seq)

    return playlist_seqs


# 음악 스크래퍼
def scrape_music_data(driver, playlist_seqs):
    data_frame_list = []
    for playlist_seq in playlist_seqs:
        driver.get(MUSIC_URL + '?plylstSeq=' + playlist_seq)
        time.sleep(WAIT_TIME)

        playlist_title = driver.find_element(By.CSS_SELECTOR, '.more_txt_title').text
        music_total = int(re.search(r'\d+', driver.find_element(By.CSS_SELECTOR, '.title .cnt').text).group())

        music_data = []

        for offset in range(1, music_total, 50):
            driver.execute_script("javascript:pageObj.sendPage('" + str(offset) + "')")
            time.sleep(WAIT_TIME)

            soup = BeautifulSoup(driver.page_source, 'lxml')
            tr_tags = soup.find_all('tr')

            for tr in tr_tags:
                td_tags = tr.find_all('td', class_='t_left')
                if td_tags and td_tags[0].find(class_='fc_gray'):
                    title = td_tags[0].find(class_='fc_gray').text.strip()
                    artist = td_tags[1].find(id='artistName').text.strip()
                    album = td_tags[2].find(class_='fc_mgray').text.strip()
                    print("Title : ", title, " / ", "Artist : ", artist, " / ", "Album : ", album)
                    music_data.append([title, artist, album])

        df = pd.DataFrame(music_data, columns=MUSIC_COLUMNS)
        data_frame_list.append({'sheet': playlist_title, 'data': df})

    return data_frame_list


# Selenium 드라이버 세팅
def init():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    return driver


# 엑셀 쓰기
def write_excel(data_frame_list, filename):
    if not os.path.exists(EXCEL_PATH):
        os.makedirs(EXCEL_PATH)

    with pd.ExcelWriter("excel/" + filename) as writer:
        for data_frame in data_frame_list:
            sheet_name = data_frame.get('sheet')

            m = re.compile(r'[\\*?:/\[\]]').search(sheet_name)
            if m:
                sheet_name = '알 수 없음'

            data_frame.get('data').to_excel(excel_writer=writer, sheet_name=sheet_name, index=False)


# 회원 키로 전체 플레이리스트 음악 가져오기
def member(member_key):
    driver = init()

    driver.get(PLAYLIST_URL + '?memberKey=' + member_key)
    playlist_total_count = int(driver.find_element(By.CSS_SELECTOR, '.no').text)

    playlist_seqs = get_playlist_seqs(driver, playlist_total_count)
    data_frame_list = scrape_music_data(driver, playlist_seqs)

    write_excel(data_frame_list, 'member_' + member_key + '_' + TODAY_DATE + '.xlsx')

    driver.quit()


# 플레이리스트 키로 음악 가져오기
def playlist(playlist_key):
    driver = init()

    playlist_seqs = [playlist_key]
    data_frame_list = scrape_music_data(driver, playlist_seqs)

    write_excel(data_frame_list, 'playlist_' + playlist_key + '_' + TODAY_DATE + '.xlsx')

    driver.quit()


if __name__ == "__main__":
    member('56195228')
