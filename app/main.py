from fastapi import FastAPI
from app import models, database
from app.routers import books, students,orders

app = FastAPI(title="Library Management System")


@app.on_event("startup")
def startup_event():
    # 确保数据库存在
    database.init_database()
    # 确保表存在
    models.Base.metadata.create_all(bind=database.engine)
    print("✅ 数据库表已确认存在！")


# 注册路由
app.include_router(books.router)
app.include_router(students.router)
app.include_router(orders.router)

@app.get("/")
def root():
    return {"message": "Welcome to Library Management System"}
