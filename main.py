# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import time
import os
import re
import openai
from fastapi import FastAPI, HTTPException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from pydantic import BaseModel

app= FastAPI()

class StoreName(BaseModel):
    name: str

class ResponseModel(BaseModel):
    summary: str




def extract_review(store_name):
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    service = ChromeService(ChromeDriverManager(driver_version="119.0.6045.105").install())
    driver = webdriver.Chrome(service=service, options=options)
    
    # 드라이버 위치 경로 입력
    driver = webdriver.Chrome(service=service, options=options)
    driver.get('https://www.naver.com')
    time.sleep(1)

    driver.find_element(By.ID, 'query').send_keys(store_name + '\n')
    time.sleep(0.3)
    area = driver.find_elements(By.XPATH,'//*[@id="place-main-section-root"]/div/section/div/div[2]/div[1]/div[2]')
    div_list = area[0].find_elements(By.XPATH,'./child::span')
    if len(div_list)==2:
        link_element = driver.find_element(By.CSS_SELECTOR, "#place-main-section-root > div > section > div > div.place_section.no_margin.OP4V8.KwSEM > div.zD5Nm.kN1U_ > div.dAsGb > span:nth-child(1) > a")
        href = link_element.get_attribute('href')
        driver.get(href)
        time.sleep(1)
    else:
        link_element = driver.find_element(By.CSS_SELECTOR, "#place-main-section-root > div > section > div > div.place_section.no_margin.OP4V8.KwSEM > div.zD5Nm.kN1U_ > div.dAsGb > span:nth-child(2) > a")
        href = link_element.get_attribute('href')
        driver.get(href)
        time.sleep(1)

    # iframe 요소 가져오는 코드
    frame = driver.find_element(By.XPATH, '//*[@id="entryIframe"]')
    # iframe 안으로 들어가는 코드
    driver.switch_to.frame(frame)
    time.sleep(1)

    try:
        for _ in range(3):
            review_tab = driver.find_element(By.CSS_SELECTOR, "#app-root > div > div > div > div:nth-child(6) > div:nth-child(3) > div.place_section.k5tcc > div.NSTUp > div > a")
            review_tab.click()
            time.sleep(0.5)
    except Exception as e:
        print('finish')
        
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    reviews = soup.find_all('span', class_='zPfVt')
    driver.quit()
    reviews = soup.find_all('span', class_='zPfVt')
    reviews = [review.text for review in reviews]
    reviews_text = ''.join(reviews)
    reviews_text = reviews_text.replace('.','')
    reviews_text = reviews_text.replace('\n','')

    return ' '.join(reviews).replace('.','').replace('\n','')

def summarize_reviews(reviews, api_key, model_id):
    openai.api_key = api_key

    response = openai.chat.completions.create(
      model=model_id,
      messages=[{"role": "system", "content": "이것은 한 식당에 대한 최근 리뷰를 보고 맛, 서비스, 분위기 등에 대해 평가하고 리뷰를 요약하는 것이다."}, 
                {"role": "user", "content": reviews}],
      max_tokens=500
    )
    return response.choices[-1].message.content

@app.post("/summarize_reviews/", response_model=ResponseModel)
def create_summary(store: StoreName):
    
    api_key = "api"
    model_id = "ft:gpt-3.5-turbo-1106:personal"
    try:
        reviews_text = extract_review(store.name)
        summary_text = summarize_reviews(reviews_text, api_key, model_id)
        return ResponseModel(summary=summary_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
