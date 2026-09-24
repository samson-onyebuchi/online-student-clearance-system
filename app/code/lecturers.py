from app.utils import *
from app.email_util import *
from flask import Flask, jsonify, Response
from flask_restful import Api, Resource, reqparse
from werkzeug.exceptions import BadRequest
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import random
import bcrypt   
import io


