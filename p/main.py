from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from typing import Optional
import os
from dotenv import load_dotenv  # dotenv 불러오기
import pymysql

load_dotenv()

def get_db_connection():
    connection = pymysql.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME"),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection
        
app = FastAPI(title="Beam Project API")

print("connect success")
    
