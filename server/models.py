from datetime import datetime
from sqlalchemy import Column, String, Integer, Table, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

user_followers = Table(
    "user_followers",
    Base.metadata,
    Column("follower_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("followed_id", Integer, ForeignKey("users.id"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(30), nullable=False)
    api_key = Column(String(30), nullable=False)

    followers = relationship(
        "User",
        secondary=user_followers,
        primaryjoin=(id == user_followers.c.followed_id),
        secondaryjoin=(id == user_followers.c.follower_id),
        back_populates="following"
    )

    following = relationship(
        "User",
        secondary=user_followers,
        primaryjoin=(id == user_followers.c.follower_id),
        secondaryjoin=(id == user_followers.c.followed_id),
        back_populates="followers"
    )

    tweets = relationship("Tweet", back_populates="author", cascade="all, delete-orphan")


class Media(Base):
    __tablename__ = "medias"

    id = Column(Integer, primary_key=True)
    file_path = Column(String, nullable=False)
    tweet_id = Column(Integer, ForeignKey("tweets.id"))

    tweet = relationship("Tweet", back_populates="medias")


class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(Integer, primary_key=True)
    tweet_data = Column(String, nullable=False)
    create_date = Column(DateTime, default=datetime.utcnow)
    author_id = Column(Integer, ForeignKey("users.id"))
    likes = Column(Integer, default=0)

    author = relationship("User", back_populates="tweets")

    medias = relationship("Media", back_populates="tweet", cascade="all, delete-orphan")