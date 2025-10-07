#!/usr/bin/env python3

from fastapi import FastAPI

app = FastAPI(title="Minimal Test API")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Minimal server is running"}