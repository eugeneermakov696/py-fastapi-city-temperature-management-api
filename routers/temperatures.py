from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import crud, schemas, models
from ..database import get_db
import httpx
import asyncio

router = APIRouter(prefix="/temperatures", tags=["temperatures"])

async def fetch_temperature(city_name: str) -> float:
    url = "https://api.open-meteo.com/v1/forecast?latitude=0&longitude=0&current_weather=true"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.json()
        return data.get("current_weather", {}).get("temperature", 20.0)

@router.post("/update")
async def update_temperatures(db: Session = Depends(get_db)):
    cities = db.query(models.City).all()
    tasks = [fetch_temperature(city.name) for city in cities]
    temps = await asyncio.gather(*tasks)
    result = []
    for city, temp in zip(cities, temps):
        record = crud.create_temperature(db, city.id, temp)
        result.append(record)
    return result

@router.get("/", response_model=list[schemas.Temperature])
def list_temperatures(city_id: int = None, db: Session = Depends(get_db)):
    return crud.get_temperatures(db, city_id)