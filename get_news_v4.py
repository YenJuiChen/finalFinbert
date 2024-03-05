from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from googletrans import Translator
import pandas as pd
import time
import csv
import requests

def fetch_news(url):
    options = webdriver.EdgeOptions()
    options.add_argument('--headless')
    service = Service(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=service, options=options)
    driver.get(url)
    time.sleep(3)  # Adjust according to your page's loading time

    # 嘗試提取新聞標題
    try:
        title_elements = driver.find_elements(By.CLASS_NAME, 'fxs_headline_tiny')[4:7]
        titles = [element.text for element in title_elements if element.text]  # 確保提取的文本非空
        if not titles:  # 如果列表為空
            print("No titles were extracted. Check the class name or webpage structure.")
        return titles
    except Exception as e:
        print(f"Error extracting titles: {e}")
    finally:
        driver.quit()

def translate_texts(texts, src='zh-cn', dest='en'):
    translator = Translator()
    translations = []
    for text in texts:
        try:
            translated = translator.translate(text, src=src, dest=dest)
            translations.append(translated.text)
        except Exception as e:
            translations.append("Translation failed")
            print(f"Translation error: {e}")
    return translations

def analyze_sentiment(texts, api_url, api_token):
    # 將新聞標題合併為一個字符串
    combined_text = " ".join(texts)
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.post(api_url, headers=headers, json={"inputs": combined_text})
    if response.status_code == 200:
        return response.json()  # 返回單一情感分析結果
    else:
        return "Sentiment analysis failed"

def save_to_csv(data, path, header):
    df = pd.DataFrame([data], columns=header)  # 修改為接受列表形式的header
    df.to_csv(path, index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    while True:
        url = "https://www.fxstreet.hk/news?q=&hPP=13&idx=FxsIndexPro&p=0&dFR%5BTags%5D%5B0%5D=%E6%AD%90%E5%85%83%2F%E7%BE%8E%E5%85%83"
        API_URL = "https://api-inference.huggingface.co/models/ProsusAI/finbert"
        API_TOKEN = "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"

        news_titles = fetch_news(url)
        translated_titles = translate_texts(news_titles, 'zh-cn', 'en')
        sentiment = analyze_sentiment(translated_titles, API_URL, API_TOKEN)

        combined_data = [news_titles, translated_titles, [sentiment]]
        save_to_csv(combined_data, "news_analysis_results.csv", ["Original Titles", "Translated Titles", "Sentiment Analysis"])

        print("Completed fetching, translating, and sentiment analysis. Results saved to CSV.")
        time.sleep(300)  # 暫停後再次執行
