from sqlmodel import Session, select
from app.database import engine
from app.models import User, UserRole

def update_balances():
    with Session(engine) as session:
        # Select all users with role STUDENT
        statement = select(User).where(User.role == UserRole.STUDENT)
        students = session.exec(statement).all()
        
        count = 0
        for student in students:
            student.balance = 50000
            session.add(student)
            count += 1
        
        session.commit()
        print(f"Successfully updated balance for {count} students.")

if __name__ == "__main__":
    update_balances()
