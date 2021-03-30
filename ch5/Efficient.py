import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import Analyzer

mk = Analyzer.MarketDB()
stocks = ['삼성전자', 'SK하이닉스', '현대자동차', 'NAVER']
df = pd.DataFrame()
for s in stocks:
    df[s] = mk.get_daily_price(s, '2019-03-01', '2021-03-01')['close'] # 약 2년 간의 네 종목 데이터 종가를 데이터프레임에 저장함

#print(df)
daily_ret = df.pct_change() # 일간 변동률을 구하는 함수 - 그 다음 날의 등락율을 알 수 있다.
annual_ret = daily_ret.mean() * 252 # daily_ret의 평균에 주식 개장일(252일)을 곱하여 연간 수익률 계산
daily_cov = daily_ret.cov() # 일간 변동률의 공분산을 구한다. - 이는 일간 리스크를 의미한다.
annual_cov = daily_cov * 252 # daily_cov에 주식 개장일(252일)을 곱하여 연간 공분산 계산

port_ret = [] 
port_risk = [] 
port_weights = []

#print(annual_cov)

for _ in range(20000): 
    weights = np.random.random(len(stocks)) # stocks에 해당하는 난수 생성
    weights /= np.sum(weights) # weights의 합을 1로 맞춰줌

    returns = np.dot(weights, annual_ret) # 비중 * 연간 수익률
    risk = np.sqrt(np.dot(weights.T, np.dot(annual_cov, weights))) # A_transpose * B와 같은 행렬을 계산하고 root 씌움

    port_ret.append(returns)
    port_risk.append(risk)
    port_weights.append(weights) # 배열에 추가

#print(port_ret)

portfolio = {'Returns': port_ret, 'Risk': port_risk} 
for i, s in enumerate(stocks): 
    portfolio[s] = [weight[i] for weight in port_weights] # 이 부분 잘 이해하기
df = pd.DataFrame(portfolio) 
df = df[['Returns', 'Risk'] + [s for s in stocks]] 

df.plot.scatter(x='Risk', y='Returns', figsize=(8, 6), grid=True)
plt.title('Efficient Frontier') 
plt.xlabel('Risk') 
plt.ylabel('Expected Returns') 
plt.show() # plotting