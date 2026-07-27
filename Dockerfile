FROM python:3.13-alpine
RUN apk add --no-cache nodejs npm sqlite
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
WORKDIR /app/frontend
RUN npm install && npm run build
WORKDIR /app
RUN python3 -c "from app.database import users_engine, UsersBase; from app.models.user import User, InvitationKey; from app.models.api_key import ApiKey; UsersBase.metadata.create_all(bind=users_engine)"
RUN python3 fill_references.py
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
