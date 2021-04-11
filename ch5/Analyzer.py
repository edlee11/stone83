import pandas as pd
import pymysql
from datetime import datetime
from datetime import timedelta
import re

class MarketDB:
    def __init__(self):
        """생성자: MariaDB 연결 및 종목코드 딕셔너리 생성"""
        self.conn = pymysql.connect(host = 'localhost', port=3306, user='root', 
            password = 'mariadb', db = 'investar',autocommit=True, charset='utf8')

        self.codes={}
        self.get_comp_info()

    def __del__(self):
        """소멸자: MariaDB 연결 해제"""
        self.conn.close()

    def get_comp_info(self):
        """company_info 테이블에서 읽어와서 codes에 저장"""
        sql = "SELECT * FROM company_info"
        krx = pd.read_sql(sql, self.conn)
        for idx in range(len(krx)):
            self.codes[krx['code'].values[idx]] = krx['company'].values[idx]

    def get_daily_price(self, code, start_date, end_date):
        """KRX 종목의 일별 시세를 데이터프레임 형태로 반환
            - code       : KRX 종목코드('005930') 또는 상장기업명('삼성전자')
            - start_date : 조회 시작일('2020-01-01'), 미입력 시 1년 전 오늘
            - end_date   : 조회 종료일('2020-12-31'), 미입력 시 오늘 날짜
        """
            
        try:
            codes_keys = list(self.codes.keys())
            codes_values = list(self.codes.values())
            
            if code in codes_values:
                idx = codes_values.index(code)
                code = codes_keys[idx]
            else:
                print(f"ValueError: Code({code}) doesn't exist.")
            
            sql = f"SELECT * FROM daily_price WHERE code = '{code}'"\
                f" and date >= '{start_date}' and date <= '{end_date}'"
            df = pd.read_sql(sql, self.conn)
            df.index = df['date']
            #df.drop()
            return df 

             
        except:
            print("Something Wrong!!")



if __name__ == "__main__":
    a = MarketDB()
    df = a.get_daily_price('삼성전자', '2020-03-14', '2020-03-30')
    print(df)