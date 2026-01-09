from fastapi import FastAPI

app = FastAPI(
    title = "Crime Vehicle Detection System",
    description = "Backend API for multi-camera vehicle tracking",
    version = "0.1.0"
)

@app.get("/")
def root():
    return{"message" : "Crime vehicle tracking backend is running"}

@app.get("/health")
def health_check():
    return{"status" : "Ok"}