# Stage 1: Costruire il frontend
FROM node:14 AS build
WORKDIR /frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend .
RUN npm run build

# Stage 2: Costruire il backend
FROM python:3.9
WORKDIR /app
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
COPY --from=build /frontend/build /app/static
COPY backend/requirements.txt .
RUN pip install -r requirements.txt
RUN pip install spotdl
COPY backend .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]