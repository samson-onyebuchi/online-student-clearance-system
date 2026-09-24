from app.utils import *
from app.email_util import *
from flask import Flask, jsonify, Response, request
from flask_restful import Api, Resource, reqparse
from werkzeug.exceptions import BadRequest
import bcrypt   
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from datetime import datetime, timedelta
import random
import io, os


