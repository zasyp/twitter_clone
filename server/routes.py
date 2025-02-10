import os
from fastapi import APIRouter
from fastapi import HTTPException, status, UploadFile
from fastapi.params import Depends
from server.database import Session, get_session
from server.models import User, Tweet, Media
from server.response_models import TweetIn, MediaUpload
from server.utils import authenticate_user

router = APIRouter()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/api/users/me", status_code=status.HTTP_200_OK)
def get_users_me(current_user: User = Depends(authenticate_user)):
    """Получение страницы залогинившегося пользователя"""
    return {
        "result": True,
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "followers": [{"id": follower.id, "name": follower.name} for follower in current_user.followers],
            "following": [{"id": followed.id, "name": followed.name} for followed in current_user.following]
        }
    }


@router.get("/api/users/{user_id}")
def get_user_by_id(user_id: int, session: Session = Depends(get_session)):
    """Получение пользователя по id"""
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "result": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "followers": [{"id": follower.id, "name": follower.name} for follower in user.followers],
            "following": [{"id": followed.id, "name": followed.name} for followed in user.following]
        }
    }


@router.post("/api/users/me", tags=["Создать нового пользователя"])
def create_user(name: str,
                api_key: str,
                session: Session = Depends(get_session)):
    """Добавление нового пользователя"""
    new_user = User(
        name=name,
        api_key=api_key
    )
    try:
        session.add(new_user)
        session.commit()
        return new_user
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))


@router.get("/api/tweets", tags=["Получение всех твитов"])
def view_all_tweets(session: Session = Depends(get_session)):
    """Получение всех твитов"""
    try:
        tweets = session.query(Tweet).all()
        result = {
            "result": True,
            "tweets": [
                {
                    "id": tweet.id,
                    "content": tweet.tweet_data,
                    "attachments": [media.file_path for media in tweet.medias],  
                    "author": {
                        "id": tweet.author.id,
                        "name": tweet.author.name,
                    },
                    "likes": [
                        {"user_id": like.id, "name": like.name}
                        for like in tweet.author.followers
                    ],
                }
                for tweet in tweets
            ],
        }

        return result


    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))


@router.post("/api/tweets", tags=["Создание нового твита"])
def post_new_tweet(tweet_in: TweetIn,
                   current_user: User = Depends(authenticate_user),
                   session: Session = Depends(get_session)
                   ):
    """Эндпоинт для создания нового твита от имени аутентифицированного пользователя"""
    new_tweet = Tweet(
        tweet_data=tweet_in.tweet_data,
        author_id=current_user.id,
    )

    try:
        session.add(new_tweet)
        session.commit()
        session.refresh(new_tweet)

        if tweet_in.tweet_media_ids:
            for media_id in tweet_in.tweet_media_ids:
                media = session.query(Media).filter(Media.id == media_id).first()
                if not media:
                    raise HTTPException(status_code=404, detail=f"Media with id {media_id} not found")

                media.tweet_id = new_tweet.id
                session.add(media)

            session.commit()

        return {
            "result": True,
            "tweet_id": new_tweet.id
        }

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))


@router.delete("/api/tweets/{id}", tags=["Удаление твита"])
def delete_tweet(id: int,
                current_user: User = Depends(authenticate_user),
                session: Session = Depends(get_session)
                ):
    """Эндпоинт позволяющий удалить выбранный твит"""
    tweet = session.query(Tweet).filter(Tweet.id == id).first()
    if not tweet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Tweet not found")
    
    if not tweet.author_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                            detail="You can only delete your tweets")

    try:
        session.delete(tweet)
        session.commit()

        return {"result": True}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))

@router.post("/api/medias", tags=["Загрузка медиафайлов"])
def upload_media(file: UploadFile,
                session: Session = Depends(get_session),
                ):
    """Эндпоинт для прикрепления и загрузки медиафайла к твиту"""
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as f:
            f.write(file.file.read())

        media = Media(file_path=file_path)
        session.add(media)
        session.commit()
        session.refresh(media)

        return {"result": True, "media_id": media.id}

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                            detail=str(e))


@router.post("/api/tweets/{id}/likes", tags=["Добавление лайка"])
def like_tweet(id: int,
               session: Session = Depends(get_session)
               ):
    """Эндпоинт для добавления лайка на выбранный твит"""
    tweet = session.query(Tweet).filter(Tweet.id == id).first() 
    if not tweet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Tweet not found")
    try:
        tweet.likes += 1
        session.commit()

        return {"result": True}
    
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))


@router.delete("/api/tweets/{id}/likes", tags=["Удаление лайка"])
def delete_like_tweet(id: int,
                      session: Session = Depends(get_session)
                      ):
    """Эндпоинт для удаления лайка с выбранного твита"""
    tweet = session.query(Tweet).filter(Tweet.id == id).first()
    if not tweet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Tweet not found")
    
    try:
        if tweet.likes > 0:
            tweet.likes -= 1
            session.commit()
            return {"result": True}
        else:
            return {"result": False, "message": "Tweet has no likes to delete"}
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))


@router.post("/api/users/{id}/follow", tags=["Подписка на пользователя"])
def follow_user(id: int,
                current_user: User = Depends(authenticate_user),
                session: Session = Depends(get_session)
                ):
    """Эндпоинт для подписки на выбранного пользователя"""
    target_user = session.query(User).filter(User.id == id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")
    
    
    if target_user in current_user.following:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="You already subscribed")
    
    try:
        current_user.following.append(target_user)
        session.commit()
        return {
            "result": True
        }
    
    except Exception as e:
        session.rollback()
        print(str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))
    

@router.delete("/api/users/{id}/follow", tags=["Отписка от пользователя"])
def follow_user(id: int,
                current_user: User = Depends(authenticate_user),
                session: Session = Depends(get_session)
                ):
    """Эндпоинт для отписки от выбранного пользователя"""
    target_user = session.query(User).filter(User.id == id).first()

    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")
    
    
    if target_user not in current_user.following:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="You are not subscribed")
    
    try:
        current_user.following.remove(target_user)
        session.commit()
        
        return {
            "result": True
        }
    
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=str(e))