from fastapi import FastAPI
from routes.home import home_route
from routes.user import user_route
from routes.ml import ml_route
from database.database import init_db
import uvicorn

app = FastAPI()
app.include_router(home_route)
app.include_router(user_route, prefix='/user')
app.include_router(ml_route, prefix='/ml')


@app.on_event("startup")
def on_startup():
    init_db()


if __name__ == '__main__':
    uvicorn.run('api:app', host='0.0.0.0', port=8080, reload=True)
