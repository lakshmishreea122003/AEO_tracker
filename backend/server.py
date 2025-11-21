# from fastapi import FastAPI, APIRouter

# from routes.AEO_tracker.router import aeo_router

# app = FastAPI()

# app.include_router(aeo_router)

# @app.get("/")
# def f():
#     return "start"



from fastapi import FastAPI
from fastapi.responses import FileResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
import matplotlib.pyplot as plt
from fastapi.middleware.cors import CORSMiddleware

from routes.AEO_tracker.router import aeo_router

import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(aeo_router)
















# create pdf


# PDF_PATH = "generated/report.pdf"
# CHART_PATH = "generated/chart.png"

# def create_pie_chart():
#     labels = ["A", "B", "C"]
#     values = [40, 30, 30]
#     plt.figure()
#     plt.pie(values, labels=labels, autopct='%1.1f%%')
#     plt.savefig(CHART_PATH)
#     plt.close()

# def create_pdf():
#     create_pie_chart()

#     doc = SimpleDocTemplate(PDF_PATH, pagesize=letter)
#     styles = getSampleStyleSheet()
#     story = []

#     story.append(Paragraph("Pie Chart Report", styles['Title']))
#     story.append(Paragraph("This chart represents category distribution.", styles['BodyText']))

#     from reportlab.platypus import Image
#     story.append(Image(CHART_PATH, width=400, height=400))

#     doc.build(story)

# @app.get("/report/pdf")
# def get_report_pdf():
#     # Generate fresh PDF on each request
#     create_pdf()

#     return FileResponse(
#         path=PDF_PATH,
#         filename="report.pdf",
#         media_type="application/pdf"
#     )
