#!/usr/bin/env python3
from public.usage import USAGE as html
from api.hello import router as hello_router
from api.quji import router as quji_router
from fastapi import FastAPI
from fastapi.responses import Response
app = FastAPI()

app.include_router(hello_router, prefix="/hello")
app.include_router(quji_router, prefix="/quji")

@app.get("/")
def _root():
    return Response(content=html, media_type="text/html")



@app.get("/quji/generate-rss")
async def generate_rss():
    xml_content = await quji_router.generate_rss()
    return Response(content=xml_content, media_type="application/rss+xml", charset="utf-8")