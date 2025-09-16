from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app import database, models, schemas
from app.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    SECRET_KEY, ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES
)

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # 仅用于文档显示；我们用 JSON 登录

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 解析并校验 Bearer access_token，要求 type=access 且 token_version 匹配
def get_current_student(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.Student:
    cred_err = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                             detail="Invalid or expired token",
                             headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise cred_err
        sid = payload.get("sub")
        tv = payload.get("tv", 0)
        if not sid:
            raise cred_err
    except JWTError:
        raise cred_err

    student = db.query(models.Student).filter(models.Student.id == int(sid)).first()
    if not student:
        raise cred_err
    # 核对 token_version
    if getattr(student, "token_version", 0) != int(tv):
        raise cred_err
    return student

@router.post("/register", response_model=schemas.StudentOut)
def register_student(data: schemas.StudentRegister, db: Session = Depends(get_db)):
    # 学号唯一检查
    exists = db.query(models.Student).filter(models.Student.student_no == data.student_no).first()
    if exists:
        raise HTTPException(status_code=400, detail="Student No already registered")

    student = models.Student(
        student_no=data.student_no,
        name=data.name,
        phone=data.phone,
        password_hash=get_password_hash(data.password),
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student

# ========= 1) 表单登录（供 Swagger Authorize 使用）=========
@router.post("/login", response_model=schemas.Token)
def login_via_form(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.student_no == form.username).first()
    # 注意：我们把 "username" 字段当作 student_no 使用
    if not student or not verify_password(form.password, student.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect student_no or password")

    access = create_access_token(student.id, getattr(student, "token_version", 0))
    refresh = create_refresh_token(student.id, getattr(student, "token_version", 0))
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}

# ========= 2) （可选保留）JSON 登录（给 Postman/前端用）=========
@router.post("/login_json", response_model=schemas.Token)
def login_via_json(credentials: schemas.StudentLogin, db: Session = Depends(get_db)):
    student = db.query(models.Student).filter(models.Student.student_no == credentials.student_no).first()
    if not student or not verify_password(credentials.password, student.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect student_no or password")

    access = create_access_token(student.id, getattr(student, "token_version", 0))
    refresh = create_refresh_token(student.id, getattr(student, "token_version", 0))
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}
# Swagger 会替你调用 /auth/login 拿到 token 并自动保存，之后所有需要授权的请求都会自动带上 Authorization: Bearer <token>
# token 隔一段时间会更新

# 用 refresh_token 换新 token（前端拿到 401 时调用；也可定时在过期前调用）
@router.post("/refresh", response_model=schemas.TokenPair)
def refresh_tokens(body: schemas.RefreshIn, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(body.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Not a refresh token")
        sid = int(payload.get("sub"))
        tv = int(payload.get("tv", 0))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    student = db.query(models.Student).filter(models.Student.id == sid).first()
    if not student:
        raise HTTPException(status_code=401, detail="Student not found")

    # 校验 token_version，防止改密后旧 refresh 继续使用
    if getattr(student, "token_version", 0) != tv:
        raise HTTPException(status_code=401, detail="Token no longer valid; please login again")

    access = create_access_token(student.id, student.token_version)
    refresh = create_refresh_token(student.id, student.token_version)   # 也可只发新的 access
    return {"access_token": access, "refresh_token": refresh, "token_type": "bearer"}


# 修改密码：需要当前登录态；成功后提升 token_version，使所有旧 token 失效
@router.post("/change_password")
def change_password(body: schemas.ChangePasswordIn,
                    me: models.Student = Depends(get_current_student),
                    db: Session = Depends(get_db)):
    # 校验旧密码
    if not verify_password(body.old_password, me.password_hash):
        raise HTTPException(status_code=400, detail="Old password incorrect")
    # （可加复杂度校验）
    me.password_hash = get_password_hash(body.new_password)
    me.token_version = (getattr(me, "token_version", 0) or 0) + 1
    db.commit()
    return {"message": "Password updated. Please login again on other devices."}


@router.get("/me", response_model=schemas.StudentOut)
def read_me(current: models.Student = Depends(get_current_student)):
    return current
