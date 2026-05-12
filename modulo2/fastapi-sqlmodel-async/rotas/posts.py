from fastapi import APIRouter, HTTPException, Depends
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlmodel import apaginate
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from modelos.post import Post, PostTag, PostBaseWithUserCommentsTags
from modelos.comment import Comment
from modelos.tag import Tag
from database import get_session
from datetime import datetime, timezone

router = APIRouter(
    prefix="/posts",  # Prefixo para todas as rotas
    tags=["Posts"],   # Tag para documentação automática
)

# Posts
@router.post("/", response_model=Post)
async def create_post(post: Post, session: AsyncSession = Depends(get_session)):
    print("Creating post:", post)
    session.add(post)
    await session.commit()
    await session.refresh(post)
    return post

@router.get("/", response_model=Page[PostBaseWithUserCommentsTags])
async def read_posts(session: AsyncSession = Depends(get_session)):
    statement = (select(Post)
                 .options(joinedload(Post.user),
                          selectinload(Post.comments).joinedload(Comment.user),
                          selectinload(Post.tags)))
    return await apaginate(session, statement, unique=False)

@router.get("/{post_id}", response_model=PostBaseWithUserCommentsTags)
async def read_post(post_id: int, session: AsyncSession = Depends(get_session)):
    statement = (select(Post).where(Post.id == post_id)
                 .options(joinedload(Post.user),
                          selectinload(Post.comments).joinedload(Comment.user),
                          selectinload(Post.tags)))
    result = await session.exec(statement)
    post = result.first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

@router.put("/{post_id}", response_model=Post)
async def update_post(post_id: int, post: Post, session: AsyncSession = Depends(get_session)):
    db_post = await session.get(Post, post_id)
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")
    for key, value in post.model_dump(exclude_unset=True).items():
        setattr(db_post, key, value)
    db_post.updated_at = datetime.now(timezone.utc)
    session.add(db_post)
    await session.commit()
    await session.refresh(db_post)
    return db_post

@router.delete("/{post_id}")
async def delete_post(post_id: int, session: AsyncSession = Depends(get_session)):
    post = await session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    await session.delete(post)
    await session.commit()
    return {"ok": True}

# Comments
@router.post("/{post_id}/comments/", response_model=Comment)
async def create_comment_for_post(post_id: int, comment: Comment, session: AsyncSession = Depends(get_session)):
    comment.post_id = post_id
    session.add(comment)
    await session.commit()
    await session.refresh(comment)
    return comment

@router.get("/{post_id}/comments/", response_model=list[Comment])
async def read_comments_for_post(post_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(Comment).where(Comment.post_id == post_id))
    return result.all()

@router.put("/{post_id}/comments/{comment_id}", response_model=Comment)
async def update_comment_for_post(post_id: int, comment_id: int, comment: Comment, session: AsyncSession = Depends(get_session)):
    db_comment = await session.get(Comment, comment_id)
    if not db_comment or db_comment.post_id != post_id:
        raise HTTPException(status_code=404, detail="Comment not found")
    for key, value in comment.model_dump(exclude_unset=True).items():
        setattr(db_comment, key, value)
    db_comment.updated_at = datetime.now(timezone.utc)
    session.add(db_comment)
    await session.commit()
    await session.refresh(db_comment)
    return db_comment

@router.delete("/{post_id}/comments/{comment_id}")
async def delete_comment_for_post(post_id: int, comment_id: int, session: AsyncSession = Depends(get_session)):
    comment = await session.get(Comment, comment_id)
    if not comment or comment.post_id != post_id:
        raise HTTPException(status_code=404, detail="Comment not found")
    await session.delete(comment)
    await session.commit()
    return {"ok": True}

# Tags
@router.post("/{post_id}/tags/", response_model=Tag)
async def create_tag_for_post(post_id: int, tag: Tag, session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(Tag).where(Tag.name == tag.name))
    tag_db = result.first()
    if tag_db:
        tag = tag_db
    else:
        session.add(tag)
        await session.commit()
        await session.refresh(tag)
    tag_dump = tag.model_dump()
    post_tag = PostTag(post_id=post_id, tag_id=tag.id)
    session.add(post_tag)
    await session.commit()
    return tag_dump

@router.get("/{post_id}/tags/", response_model=list[Tag])
async def read_tags_for_post(post_id: int, session: AsyncSession = Depends(get_session)):
    statement = select(Tag).join(PostTag).where(PostTag.post_id == post_id)
    result = await session.exec(statement)
    return result.all()

@router.put("/{post_id}/tags/{tag_id}", response_model=Tag)
async def update_tag_for_post(post_id: int, tag_id: int, tag: Tag, session: AsyncSession = Depends(get_session)):
    db_tag = await session.get(Tag, tag_id)
    if not db_tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    for key, value in tag.model_dump(exclude_unset=True).items():
        setattr(db_tag, key, value)
    session.add(db_tag)
    await session.commit()
    await session.refresh(db_tag)
    return db_tag

@router.delete("/{post_id}/tags/{tag_id}")
async def delete_tag_for_post(post_id: int, tag_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(PostTag).where(PostTag.post_id == post_id, PostTag.tag_id == tag_id))
    post_tag = result.first()
    if not post_tag:
        raise HTTPException(status_code=404, detail="Tag not found for this post")
    await session.delete(post_tag)
    await session.commit()
    return {"ok": True}
