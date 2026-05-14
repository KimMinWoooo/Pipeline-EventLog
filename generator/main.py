import os
import time
import random
import json
import psycopg2
from datetime import datetime, timedelta

def get_db_connection():
    # DB 컨테이너가 준비될 때까지 재시도하며 연결을 시도하는 로직
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
            # Docker Compose 실행 시 DB 서비스가 뜨는 속도보다 앱이 빠를 수 있으므로 재시도 필요
            print("Database not ready, retrying in 2 seconds...")
            time.sleep(2)

def populate_users(cur):
    # 마스터 데이터(users)를 먼저 생성하여 RDBMS의 참조 무결성을 보장
    print("Populating master data: users...")
    membership_levels = ['Gold', 'Silver', 'Bronze']
    user_data = []
    for i in range(1, 21):
        user_id = f"user_{i:03d}"
        name = f"Customer_{i:03d}"
        level = random.choice(membership_levels)
        user_data.append((user_id, name, level))
    
    # ON CONFLICT를 사용하여 중복 실행 시에도 에러가 발생하지 않도록 함 (Idempotency)
    cur.executemany(
        "INSERT INTO users (user_id, name, membership_level) VALUES (%s, %s, %s) ON CONFLICT (user_id) DO NOTHING",
        user_data
    )

def generate_events(cur, num_events=500):
    # 실제 사용자 행동인 트랜잭션 데이터를 생성
    print(f"Generating {num_events} transaction events...")
    event_types = ['page_view', 'add_to_cart', 'purchase', 'error']
    devices = ['mobile', 'desktop', 'tablet']
    sources = ['google', 'facebook', 'direct', 'email']
    pages = ['/home', '/products', '/cart', '/checkout']
    
    # 외래키 제약조건을 지키기 위해 실제 존재하는 user_id 목록을 먼저 가져옴
    cur.execute("SELECT user_id FROM users")
    user_ids = [row[0] for row in cur.fetchall()]

    for i in range(num_events):
        user_id = random.choice(user_ids)
        # 세션 ID를 통해 유저 행동의 흐름(Flow)을 추적할 수 있도록 설계
        session_id = f"sess_{user_id}_{random.randint(1, 5)}"
        event_type = random.choice(event_types)
        event_time = datetime.now() - timedelta(minutes=random.randint(0, 2000))
        
        properties = {}
        # JSONB 필드를 활용하여 이벤트 타입별로 서로 다른 구조의 상세 데이터를 유연하게 저장
        if event_type == 'purchase':
            properties = {"revenue": random.randint(10000, 100000), "item_count": random.randint(1, 5)}
        elif event_type == 'error':
            properties = {"code": 500, "msg": "Internal Server Error"}

        cur.execute(
            """
            INSERT INTO event_logs (
                event_type, user_id, session_id, event_time, 
                page_url, traffic_source, device_type, properties
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                event_type, user_id, session_id, event_time,
                random.choice(pages), random.choice(sources), random.choice(devices),
                json.dumps(properties)
            )
        )
        if (i+1) % 100 == 0:
            print(f"Inserted {i+1} events...")

def main():
    conn = get_db_connection()
    cur = conn.cursor()
    
    populate_users(cur)
    conn.commit()
    
    generate_events(cur)
    conn.commit()
    
    cur.close()
    conn.close()
    print("Database seeding complete.")

if __name__ == "__main__":
    main()
