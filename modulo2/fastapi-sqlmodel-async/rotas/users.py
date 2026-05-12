from fastapi import APIRouter, HTTPException, Depends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import apaginate
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from modelos.user import User
from database import get_session

router = APIRouter(
    prefix="/users",  # Prefixo para todas as rotas
    tags=["Users"],   # Tag para documentação automática
)

# Users
@router.post("/", response_model=User)
async def create_user(user: User, session: AsyncSession = Depends(get_session)):
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

@router.get("/", response_model=Page[User])
async def read_users(session: AsyncSession = Depends(get_session)):
    return await apaginate(session, select(User))

@router.get("/{user_id}", response_model=User)
async def read_user(user_id: int, session: AsyncSession = Depends(get_session)):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=User)
async def update_user(user_id: int, user: User, session: AsyncSession = Depends(get_session)):
    db_user = await session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in user.model_dump(exclude_unset=True).items():
        setattr(db_user, key, value)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

@router.delete("/{user_id}")
async def delete_user(user_id: int, session: AsyncSession = Depends(get_session)):
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await session.delete(user)
    await session.commit()
    return {"ok": True}
