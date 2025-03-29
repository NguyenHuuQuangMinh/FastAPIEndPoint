from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, model_validator
from typing import List
import httpx
from datetime import datetime

app = FastAPI()

class WeatherRequest(BaseModel):
    lon: float = Field(..., description="Kinh độ")
    lat: float = Field(..., description="Vĩ độ")
    start_year: int = Field(..., ge=1950, description="Năm bắt đầu (tối thiểu 1950)")
    end_year: int = Field(..., ge=1950, description="Năm kết thúc")

    @model_validator(mode="after")
    def validate_years(self):
        current_year = datetime.now().year
        if self.end_year < self.start_year:
            raise HTTPException(status_code=422, detail="Năm kết thúc phải lớn hơn hoặc bằng năm bắt đầu.")
        if self.end_year > current_year:
            raise HTTPException(status_code=422, detail=f"Năm kết thúc không thể lớn hơn năm hiện tại ({current_year}).")
        if self.start_year > current_year:
            raise HTTPException(status_code=422, detail=f"Năm bắt đầu không thể lớn hơn năm hiện tại ({current_year}).")
        
        return self

class WeatherResponse(BaseModel):
    header: List[str] = ["day", "month", "year", "doy", "max_temp", "min_temp", "precip"]
    value: List[List[float]]

@app.post("/weather", response_model=WeatherResponse)
async def get_weather(request: WeatherRequest):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://archive-api.open-meteo.com/v1/archive",
                params={
                    "latitude": request.lat,
                    "longitude": request.lon,
                    "start_date": f"{request.start_year}-01-01",
                    "end_date": f"{request.end_year}-12-31",
                    "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
                    "timezone": "auto",
                },
            )
            response.raise_for_status()
            data = response.json().get("daily", {})

            value = [
                [
                    int(date.split("-")[2]),  # day
                    int(date.split("-")[1]),  # month
                    int(date.split("-")[0]),  # year
                    index + 1,                # doy (day of year)
                    t_max,                    # max_temp
                    t_min,                    # min_temp
                    precip                    # precipitation
                ]
                for index, (date, t_max, t_min, precip) in enumerate(
                    zip(data["time"], data["temperature_2m_max"], data["temperature_2m_min"], data["precipitation_sum"])
                )
            ]

            return WeatherResponse(value=value)

    except httpx.HTTPStatusError as http_err:
        raise HTTPException(status_code=response.status_code, detail=f"Lỗi từ Open-Meteo API: {http_err}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi máy chủ nội bộ: {e}")
