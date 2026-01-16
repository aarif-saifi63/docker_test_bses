from flask import jsonify
from Models.division_model import Divisions
from database import SessionLocal


def get_divisions():
    try:
        db = SessionLocal()
        divisions = db.query(Divisions).all()

        if not divisions:
            return jsonify({"message": "No divisions found"}), 404

        division_list = []
        for div in divisions:
            division_list.append({
                "id": div.id,
                "division_code": div.division_code,
                "division_name": div.division_name
            })

        return jsonify({"data": division_list, "message": "featch division successfully", "status": True, "count": len(division_list)}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500