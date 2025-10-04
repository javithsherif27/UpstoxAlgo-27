from fastapi import HTTPException

def unauthorized():
    raise HTTPException(status_code=401, detail="Unauthorized")
