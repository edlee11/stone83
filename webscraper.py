from bs4 import BeautifulSoup
from urllib.request import urlopen
import pandas as pd
import requests
from matplotlib import pyplot as plt
import mplfinance as mpf


url = 'https://finance.naver.com/item/sise_day.nhn?code=005930&page=1'

with urlopen(url) as doc:
    html = BeautifulSoup(requests.get(url, headers={'User-agent': 'Mozilla/5.0'}).text, "lxml")
    pgrr = html.find('td', class_ = 'pgRR')
    s=str(pgrr.a['href']).split('=')
    last_page = s[-1]
    #print(last_page)

df = pd.DataFrame()
sise_url = 'https://finance.naver.com/item/sise_day.nhn?code=005930'

for page in range(1,int(last_page)+1):
    page_url = '{}&page={}'.format(sise_url,page)
    response_page = requests.get(page_url, headers ={'User-agent': 'Mozilla/5.0'}).text
    df = df.append(pd.read_html(response_page)[0])

df = df.dropna()
df = df.iloc[0:30]
df = df.rename(columns={'날짜':'Date', '시가':'Open', '고가':'High', '저가':'Low', '종가':'Close', '거래량':'Volume'})
df = df.sort_values(by='Date')
df.index = pd.to_datetime(df.Date)
df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

"""plt.title('Celltrion(close)')
plt.xticks(rotation=45)
plt.plot(df['날짜'], df['종가'], 'co-')
plt.grid(color = 'gray', linestyle='--')
plt.show()"""

kwargs = dict(title='Samsung electronics', type='candle',mav=(2,4,6), volume=True, ylabel='ohlc candles')
mc = mpf.make_marketcolors(up='r', down='b', inherit = True)
s = mpf.make_mpf_style(marketcolors=mc)
mpf.plot(df, **kwargs, style=s)

print("test")

#mpf.plot(df, title="Celltrion", type='ohlc')