import requests

def fetch_30days_data_from_api(city):
    headers = {
        'Authorization': 'bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwczovL2FpcnF1YWxpdHkuYXFpLmluL2FwaS92MS9sb2dpbiIsImlhdCI6MTczMzkzMjk3NCwiZXhwIjoxNzM1MTQyNTc0LCJuYmYiOjE3MzM5MzI5NzQsImp0aSI6InZ6bWVnbXZPaFdENEROTzkiLCJzdWIiOiIyOTE2OCIsInBydiI6IjIzYmQ1Yzg5NDlmNjAwYWRiMzllNzAxYzQwMDg3MmRiN2E1OTc2ZjcifQ.8c3DonF0pKz3d58_4RYzThjA6KNxqQjAXaiMFfpmkm0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json',
        'searchtype': "cityId",
        'locationid': city,
        'sendevid': "AQI-IN"
    }
    try:
        response = requests.get("https://airquality.aqi.in/api/v1/getLastMonthHistory", headers=headers)
        if response.status_code == 200:
            json_data = response.json()
            print(f"Data fetched for city: {city}")
            return json_data
        else:
           return f"Failed to fetch data for city: {city}. Status code: {response.status_code}"
    except Exception as e:
        return f"Error during API call for city {city}: {e}"
    
print(fetch_30days_data_from_api("Raipur"))