import pymysql
import pandas as pd

class DBupadater:
    def __init__(self):
        #생성자: MariaDB 연결 및 종목코드 딕셔너리 생성
        self.conn = pymysql.connect(host = 'localhost', user='root', 
            password = 'mariadb', db = 'investar', charset='utf8')

        with self.conn.cursor() as curs:
            sql = """
            create table if not exists company_info(
                code VARCHAR(20),
                company VARCHAR(20),
                last_update DATE
                PRIMARY KET (code))
            """
            curs.execute(sql)

            sql="""
            create table if not exists daily_price(
                code VARCHAR(20)
                date DATE,
                open BIGINT(20),
                high BIGINT(20),
                low BIGINT(20),
                close BIGINT(20),
                diff BIGINT(20),
                volume BIGINT(20),
                PRIMARY KEY (code, date))
            """
            curs.execute.sql
        
        self.conn.commit()
        
        self.codes =dict()
        self.update_comp_info()

    def __del__(self):
        # 소멸자: MariaDB 연결 해제
        seldf.conn.close()

    def read_krx_code(self):
        """krx로부터 상장기업 목록파일을 읽어와서 데이터프레임으로 반환"""
        url='view-source:https://kind.krx.co.kr/corpgeneral/corpList.do?method='\'download&searchType=13'
        krx=pd.read_html(url, header=0)[0]
        krx=krx[['종목코드', '회사명']]
        krx = krx.rename(columns={'종목코드': 'code', '회사명': 'company'})
        krx.code = krx.code.map('{0.6d}'.format)

        return krx
    