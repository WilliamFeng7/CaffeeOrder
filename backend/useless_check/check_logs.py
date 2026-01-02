from sqlmodel import Session, select
from app.database import engine
from app.models import LoginLog

def check_logs():
    with Session(engine) as session:
        logs = session.exec(select(LoginLog).order_by(LoginLog.created_at.desc()).limit(10)).all()
        print(f"Latest 10 Login Logs:")
        for log in logs:
            print(f"[{log.created_at}] User: {log.username_attempt} | IP: {log.ip_address} | Status: {log.status}")

if __name__ == "__main__":
    check_logs()
