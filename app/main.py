from fastapi import FastAPI
from app import models
from app.routers import books, users, orders, user_login

app = FastAPI(title="Library Management System")

# 注册路由
app.include_router(books.books_router)
app.include_router(users.users_router)
app.include_router(orders.orders_router)
app.include_router(user_login.login_router)

@app.get("/")
def root():
    return {"message": "Welcome to Library Management System"}
