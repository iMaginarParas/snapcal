from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from jose import JWTError, jwt

from .. import database
from ..models.user import User
from ..schemas import schemas
from ..utils import auth_utils
from ..utils.limiter import limiter
from ..services.analytics_service import track_event, identify_user
from ..services.metrics_service import record_metric

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, auth_utils.SECRET_KEY, algorithms=[auth_utils.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=schemas.UserOut)
@limiter.limit("5/minute")
def register(request: Request, user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    print(f"DEBUG: Registration attempt for email: {user.email}")
    try:
        db_user = db.query(User).filter(User.email == user.email).first()
        if db_user:
            print(f"DEBUG: Registration failed - Email already exists: {user.email}")
            raise HTTPException(status_code=400, detail="Email already registered")
        
        hashed_password = auth_utils.get_password_hash(user.password)
        new_user = User(email=user.email, password_hash=hashed_password)
        
        print("DEBUG: Adding new user to database...")
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print(f"DEBUG: User created successfully with ID: {new_user.id}")

        try:
            identify_user(user_id=new_user.id, properties={"email": new_user.email})
            track_event(user_id=new_user.id, event_name="user_registered")
        except Exception as e:
            print(f"DEBUG: Analytics tracking failed (non-critical): {str(e)}")

        return new_user
    except Exception as e:
        print(f"ERROR during registration: {str(e)}")
        # If it's already an HTTPException, re-raise it
        if isinstance(e, HTTPException):
            raise e
        # Otherwise, raise a 500 with the error detail
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.post("/login", response_model=schemas.Token)
@limiter.limit("5/minute")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not auth_utils.verify_password(form_data.password, user.password_hash):
        # Log failed login for security monitoring
        record_metric("security_event", tags={"type": "login_failure", "user": form_data.username})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    track_event(user_id=user.id, event_name="user_logged_in")

    access_token_expires = timedelta(minutes=auth_utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_utils.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=schemas.UserOut)
def update_profile(
    profile_data: schemas.UserProfileUpdate,
    db: Session = Depends(database.get_db),
    current_user: User = Depends(get_current_user)
):
    if profile_data.height is not None:
        current_user.height = profile_data.height
    if profile_data.weight is not None:
        current_user.weight = profile_data.weight
    if profile_data.age is not None:
        current_user.age = profile_data.age
    if profile_data.gender is not None:
        current_user.gender = profile_data.gender
        
    db.commit()
    db.refresh(current_user)
    return current_user
