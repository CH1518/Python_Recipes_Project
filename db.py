from sqlalchemy import JSON, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import sessionmaker, backref, relationship

engine = create_engine('postgresql+psycopg2://python:password@localhost/recipe', echo = True)
Base = declarative_base()
Session = sessionmaker(bind = engine)
session = Session()

class URL(Base):
    __tablename__ = "url"
    id = Column(Integer, primary_key = True)
    url = Column(String)
    recipe_name = Column(String)
    image = Column(String)
    skip = Column(Boolean)

class Recipe(Base):
    __tablename__ = "recipe"
    id = Column(Integer, primary_key = True)
    url_id = Column(Integer, ForeignKey('url.id'))
    author = Column(String)
    description = Column(String)
    recipe = Column(JSON)

    url = relationship("URL", backref = backref("recipe", uselist = False))

Base.metadata.create_all(engine)