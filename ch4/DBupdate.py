import pandas as pd
from bs4 import BeautifulSoup
import urllib, pymysql, calendar, time, json
from urllib.request import urlopen
from datetime import datetime
from threading import Timer
import requests

class DBupdater:
    def __init__(self):
        #생성자: MariaDB 연결 및 종목코드 딕셔너리 생성
        self.conn = pymysql.connect(host = 'localhost', port=3306, user='root', 
            password = 'mariadb', db = 'investar',autocommit=True, charset='utf8')

        with self.conn.cursor() as curs:
            sql = """
            CREATE TABLE IF NOT EXISTS company_info(
                code VARCHAR(20),
                company VARCHAR(40),
                last_update DATE,
                PRIMARY KEY (code))
            """
            curs.execute(sql)

            sql="""
            CREATE TABLE IF NOT EXISTS daily_price(
                code VARCHAR(20),
                date DATE,
                open BIGINT(20),
                high BIGINT(20),
                low BIGINT(20),
                close BIGINT(20),
                diff BIGINT(20),
                volume BIGINT(20),
                PRIMARY KEY (code, date))
            """
            curs.execute(sql)
        
        self.conn.commit()
        self.codes = dict()

    def __del__(self):
        # 소멸자: MariaDB 연결 해제
        self.conn.close()

    def read_krx_code(self):
        """krx로부터 상장기업 목록파일을 읽어와서 데이터프레임으로 반환"""
        url = 'http://kind.krx.co.kr/corpgeneral/corpList.do?method='\
            'download&searchType=13'
        krx=pd.read_html(url, header=0)[0]
        krx=krx[['종목코드', '회사명']]
        krx = krx.rename(columns={'종목코드': 'code', '회사명': 'company'})
        krx.code = krx.code.map('{:06d}'.format)

        return krx

    def update_comp_info(self):
        """종목코드를 company_info 테이블에 업데이트 한 후 딕셔너리에 저장"""
        sql = "SELECT * FROM company_info"
        df = pd.read_sql(sql, self.conn)
        for idx in range(len(df)):
            self.codes[df['code'].values[idx]] = df['company'].values[idx] # company_info 테이블에 저장되어 있던 정보를 self.codes 딕셔너리에 저장하는 과정

        print(self.conn)
        print(df)

        with self.conn.cursor() as curs:
            sql = "SELECT max(last_update) FROM company_info" #last_update한 중 제일 최근 시간
            curs.execute(sql)
            rs = curs.fetchone()
            today = datetime.today().strftime('%Y-%m-%d') # 날짜나 시간을 string으로 형변환

            if rs[0] == None or rs[0].strftime('%Y-%m-%d') < today: # fetch한 적이 없거나 fetch한 날이 오늘보다 이전인 경우
                    krx = self.read_krx_code()
                    for idx in range(len(krx)):
                        code = krx.code.values[idx]
                        company = krx.company.values[idx]
                        sql = f"REPLACE INTO company_info (code, company, last_update) VALUES ('{code}', '{company}', '{today}')"
                        print(self.conn)
                        curs.execute(sql)
                        self.codes[code] = company # 실질적인 update code
                        tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')
                        print(f"[{tmnow}] #{idx+1:04d} REPLACE INTO company_info "\
                            f"VALUES ({code}, {company}, {today})") # 단지 code, company, today가 변경되었다는 메시지를 출력해 주는 것임
                    self.conn.commit()
                    print('')    
    

    def read_naver(self, code, company, pages_to_fetch):
        """네이버에서 주식 시세를 읽어서 데이터프레임으로 반환"""
        try:
            url = f"http://finance.naver.com/item/sise_day.nhn?code={code}" # 예시 : 셀트리온 code - 068270
            html = BeautifulSoup(requests.get(url, headers={'User-agent' : 'Mozilla/5.0'}).text, "lxml")# 2021년부터 네이버에서 크롤링을 제한하였기 때문에 header설정을 다음과 같이 해주어야 한다.
            pgrr = html.find("td", class_="pgRR") # 사이트의 페이지 소스코드보기 누르면 맨 마지막 장을 찾는 것을 확인할 수 있다.
            if pgrr is None:
                return None
            s = str(pgrr.a["href"]).split('=')
            lastpage = s[-1] # 마지막 페이지 번호 저장
            df = pd.DataFrame()
            pages = min(int(lastpage), pages_to_fetch) # '최대 페이지 수'와 'fetch할 만큼 제한한 페이지 수' 중 작은 값 선택
            for page in range(1, pages + 1):
                pg_url = '{}&page={}'.format(url, page) # 해당 페이지로 이동
                df = df.append(pd.read_html(requests.get(pg_url, headers={'User-agent' : 'Mozilla/5.0'}).text)[0])
                tmnow = datetime.now().strftime('%Y-%m-%d %H:%M')
                print('[{}] {} ({}) : {:04d}/{:04d} pages are downloading...'.
                    format(tmnow, company, code, page, pages), end="\r")
            df = df.rename(columns={'날짜':'date','종가':'close','전일비':'diff'
                ,'시가':'open','고가':'high','저가':'low','거래량':'volume'})
            df['date'] = df['date'].replace('.', '-') #date 데이터 형태 변경(.->-)
            df = df.dropna()
            df[['close', 'diff', 'open', 'high', 'low', 'volume']] = df[['close',
                'diff', 'open', 'high', 'low', 'volume']].astype(int)
            df = df[['date', 'open', 'high', 'low', 'close', 'diff', 'volume']]
        
        except Exception as e:
            print('Exception occured :', str(e))
            return None

        return df

    def replace_into_db(self, df, num, code, company):
        """네이버에서 읽어온 주식 시세를 DB에 REPLACE"""
        with self.conn.cursor() as curs:
            for r in df.itertuples():
                sql = f"REPLACE INTO daily_price VALUES ('{code}', "\
                    f"'{r.date}', {r.open}, {r.high}, {r.low}, {r.close}, "\
                    f"{r.diff}, {r.volume})" # daily_price 데이터베이스에 값을 저장하는 query
                curs.execute(sql)
            self.conn.commit()
            print('[{}] #{:04d} {} ({}) : {} rows > REPLACE INTO daily_'\
                'price [OK]'.format(datetime.now().strftime('%Y-%m-%d'\
                ' %H:%M'), num+1, company, code, len(df)))

    def update_daily_price(self, pages_to_fetch):
        """KRX 상장법인의 주식 시세를 네이버로부터 읽어서 DB에 업데이트"""  
        for idx, code in enumerate(self.codes):
            df = self.read_naver(code, self.codes[code], pages_to_fetch) #네이버에서 정보를 가져와서 df에 저장
            if df is None:
                continue
            self.replace_into_db(df, idx, code, self.codes[code]) #df의 정보를 쿼리를 통하여 데이터베이스에 저장


    def execute_daily(self):
        """실행 즉시 및 매일 오후 다섯시에 daily_price 테이블 업데이트"""
        self.update_comp_info()
        
        try:
            with open('config.json', 'r') as in_file:
                config = json.load(in_file) 
                pages_to_fetch = config['pages_to_fetch'] #아래 코드에서 pages_to_fetch가 1로 설정되어 있다.
        except FileNotFoundError: # 'config.json'파일이 존재하지 않는 경우
            with open('config.json', 'w') as out_file:
                pages_to_fetch = 100 
                config = {'pages_to_fetch': 1} #초기값은 100이고 그 다음부터는 1로 설정하여 페이지를 읽어온다.
                json.dump(config, out_file)
        self.update_daily_price(pages_to_fetch) #여기까지가 company_info와 daily_price 데이터베이스 업데이트 과정

        tmnow = datetime.now()
        lastday = calendar.monthrange(tmnow.year, tmnow.month)[1]
        if tmnow.month == 12 and tmnow.day == lastday:
            tmnext = tmnow.replace(year=tmnow.year+1, month=1, day=1,
                hour=17, minute=0, second=0)
        elif tmnow.day == lastday:
            tmnext = tmnow.replace(month=tmnow.month+1, day=1, hour=17,
                minute=0, second=0)
        else:
            tmnext = tmnow.replace(day=tmnow.day+1, hour=17, minute=0,
                second=0)
        tmdiff = tmnext - tmnow
        secs = tmdiff.seconds
        t = Timer(secs, self.execute_daily)
        print("Waiting for next update ({}) ... ".format(tmnext.strftime
            ('%Y-%m-%d %H:%M')))
        t.start()

if __name__ == '__main__':
    dbu = DBupdater()
    dbu.update_comp_info()
    dbu.update_daily_price(1)