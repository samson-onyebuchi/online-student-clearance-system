from flask import Flask
from flask_restful import Api, Resource
from pymongo import MongoClient

app = Flask(__name__)
api = Api(app)


# MongoDB connection
client = MongoClient("mongodb+srv://student_clearance_user:sprnDxLQI12Ot3Uc@cluster0.qkfd03b.mongodb.net/")

db = client["StudentClearanceDB"]
students = db["students"]


# Get all students
class GetStudents(Resource):

    def get(self):
        data = list(students.find({}, {"_id": 0}))

        return {
            "success": True,
            "message": "Students retrieved successfully",
            "data": data
        }, 200


# API Resource
api.add_resource(GetStudents, "/api/v1/students")


# Run application
if __name__ == "__main__":
    app.run(debug=True)