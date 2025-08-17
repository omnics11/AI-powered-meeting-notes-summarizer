# app/main.py
import os
from fastapi import FastAPI, Request, UploadFile, Form
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from app.db import SessionLocal, init_db, Summary
from app.ai_client import AIClient
from app.emailer import send_email

load_dotenv()
app = FastAPI(title="SocialHub Summarizer")
templates = Jinja2Templates(directory="templates")

# (optional) static dir if you add CSS later
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# init DB on startup
@app.on_event("startup")
def _startup():
    init_db()

@app.get("/")
def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate")
async def post_generate(
    request: Request,
    instruction: str = Form(...),
    file: UploadFile | None = None,
    transcript_text: str = Form(""),
):
    """
    Accept either a text file upload OR pasted text (transcript_text).
    """
    transcript = transcript_text.strip()
    if not transcript and file:
        content_bytes = await file.read()
        transcript = content_bytes.decode("utf-8", errors="ignore")

    if not transcript:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Please upload a transcript or paste text."},
            status_code=400,
        )

    # Call LLM
    ai = AIClient()
    summary_text = ai.summarize(instruction=instruction, transcript=transcript)

    # Save in DB
    db = SessionLocal()
    record = Summary(
        instruction=instruction,
        transcript=transcript,
        summary=summary_text,
        recipients="",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    db.close()

    return RedirectResponse(url=f"/summary/{record.id}", status_code=303)

@app.get("/summary/{summary_id}")
def get_summary(request: Request, summary_id: int):
    db = SessionLocal()
    rec = db.query(Summary).filter(Summary.id == summary_id).first()
    db.close()
    if not rec:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Summary not found."},
            status_code=404,
        )
    return templates.TemplateResponse("summary.html", {"request": request, "rec": rec})

@app.post("/summary/{summary_id}/update")
async def post_update_summary(
    request: Request,
    summary_id: int,
    summary: str = Form(...),
    recipients: str = Form(""),
):
    db = SessionLocal()
    rec = db.query(Summary).filter(Summary.id == summary_id).first()
    if not rec:
        db.close()
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Summary not found."},
            status_code=404,
        )
    rec.summary = summary
    rec.recipients = recipients
    db.commit()
    db.refresh(rec)
    db.close()
    return RedirectResponse(url=f"/summary/{summary_id}", status_code=303)

@app.post("/summary/{summary_id}/send")
async def post_send_summary(request: Request, summary_id: int):
    db = SessionLocal()
    rec = db.query(Summary).filter(Summary.id == summary_id).first()
    if not rec:
        db.close()
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": "Summary not found."},
            status_code=404,
        )

    # 🔹 Get recipient from the form
    form = await request.form()
    recipient = form.get("recipient")

    if not recipient:
        db.close()
        return templates.TemplateResponse(
            "summary.html",
            {"request": request, "rec": rec, "error": "Please enter recipient email."},
            status_code=400,
        )

    # 🔹 Save recipient(s) into the DB
    rec.recipients = recipient
    db.add(rec)
    db.commit()
    db.refresh(rec)
    db.close()

    # 🔹 Send email
    send_email(
        subject="Meeting Summary",
        body=rec.summary,
        recipients_csv=rec.recipients,
    )

    return templates.TemplateResponse(
        "summary.html",
        {"request": request, "rec": rec, "sent": True},
    )
