
# 저장된 로그를 분석 및 차트 생성 코드 작성

import os
import time
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt

def get_db_connection():
    while True:
        try:
            conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'eventlog'),
                user=os.getenv('DB_USER', 'user'),
                password=os.getenv('DB_PASSWORD', 'password')
            )
            return conn
        except psycopg2.OperationalError:
            print("Database not ready, retrying in 2 seconds...")
            time.sleep(2)

def analyze():
    conn = get_db_connection()
    
    # 데이터가 충분히 쌓일 때까지 대기 (Generator와의 동기화)
    print("Waiting for data (checking if users and logs are ready)...")
    while True:
        try:
            df_check = pd.read_sql("SELECT (SELECT COUNT(*) FROM users) as u, (SELECT COUNT(*) FROM event_logs) as e", conn)
            if df_check.iloc[0, 0] >= 20 and df_check.iloc[0, 1] >= 500:
                break
        except:
            pass
        time.sleep(3)
    
    print("Executing RDBMS JOIN Analysis...")

    # Query 1: JOIN을 활용한 멤버십 등급별 매출 기여도 분석
    # 마스터 테이블(users)과 로그 테이블(event_logs)을 결합하여 고차원 인사이트 도출
    query_membership_revenue = """
        SELECT 
            u.membership_level,
            SUM((e.properties->>'revenue')::numeric) as total_revenue, -- JSONB 필드 내 매출 데이터 추출 및 형변환
            COUNT(DISTINCT u.user_id) as user_count
        FROM event_logs e
        JOIN users u ON e.user_id = u.user_id
        WHERE e.event_type = 'purchase'
        GROUP BY u.membership_level
        ORDER BY total_revenue DESC
    """
    df_revenue = pd.read_sql(query_membership_revenue, conn)

    # Query 2: 트래픽 소스별 세션 분포
    # 단순 로그 수가 아닌 '고유 세션 수(DISTINCT session_id)'를 카운트하여 실제 방문 품질 측정
    query_traffic = """
        SELECT traffic_source, COUNT(DISTINCT session_id) as session_count
        FROM event_logs
        GROUP BY traffic_source
        ORDER BY session_count DESC
    """
    df_traffic = pd.read_sql(query_traffic, conn)

    # 시각화
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    # 차트 1: 멤버십 등급별 매출
    ax1.bar(df_revenue['membership_level'], df_revenue['total_revenue'], color=['#FFD700', '#C0C0C0', '#CD7F32'])
    ax1.set_title('멤버십 등급별 매출', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Total Revenue')

    # 차트 2: 트래픽 소스별 세션 비중
    ax2.pie(df_traffic['session_count'], labels=df_traffic['traffic_source'], autopct='%1.1f%%', startangle=140)
    ax2.set_title('트래픽 소스별 세션 비중', fontsize=14, fontweight='bold')

    plt.tight_layout()
    output_path = '/output/rdbms_analysis.png'
    plt.savefig(output_path, dpi=300)
    print(f"Analysis complete. Result saved to {output_path}")
    conn.close()

if __name__ == "__main__":
    time.sleep(5)
    analyze()
