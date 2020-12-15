import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from  sqlalchemy.sql.expression import func, select
from flask_cors import CORS, cross_origin
import random

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
  app = Flask(__name__)
  CORS(app)
  setup_db(app)

  cors = CORS(app, resources={r"*": {"origins": "*"}})

  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
      response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
      return response

  @app.route('/api/categories')
  def categories():
    categoriesQuery = db.session.query(Category).all()
    categories = {}
    for z in categoriesQuery:
        categories[z.id] = z.type
    return jsonify(categories)

  @app.route('/api/questions')
  def questions():
      if request.args.get('page'):
          pageNo = int(request.args.get('page')) - 1
      else:
        pageNo = 0
      questions = db.session.query(Question).limit(10).offset(pageNo*QUESTIONS_PER_PAGE)
      totalCount = db.session.query(Question).count()
      categoriesQuery = db.session.query(Category).all()
      categories = {}
      for z in categoriesQuery:
          categories[z.id] = z.type

      return jsonify(categories=categories,total_questions=totalCount,questions=[z.format() for z in questions])

  @app.route('/api/questions/<questionid>', methods=["DELETE"])
  def deleteQuestion(questionid):
      db.session.query(Question).filter_by(id = questionid).delete()
      try:
          db.session.commit()
          return jsonify(result="Deleted Sucessfully")
      except Exception as e:
          db.session.rollback()
          db.session.flush()
          abort(500)

  @app.route('/api/questions', methods=["POST"])
  def addQuestion():
      questionData = request.json
      newQuestion = Question(questionData["question"],questionData["answer"],questionData["category"],questionData["difficulty"])
      db.session.add(newQuestion)
      try:
          db.session.commit()
          return jsonify(result=newQuestion.format())
      except Exception as e:
          db.session.rollback()
          db.session.flush()
          abort(500)

  @app.route('/api/questions/search', methods=["POST"])
  def questions_search():
      query = request.json["searchTerm"]
      questions = Question.query.filter(Question.question.ilike('%{query}%')).all()
      totalCount = len(questions)
      return jsonify(total_questions=totalCount,questions=[z.format() for z in questions])

  @app.route('/api/categories/<categoryid>/questions')
  def questionsForCategory(categoryid):
     questions = db.session.query(Question).filter_by(category=categoryid)
     totalCount = len(questions)
     return jsonify(current_category=categoryid,total_questions=totalCount,questions=[z.format() for z in questions])


  @app.route('/api/quizzes', methods=["POST"])
  def runquiz():
      previous = request.json["previous_questions"]
      category = request.json["quiz_category"]["id"]
      previous_subquery = db.session.query(Question.id).filter(Question.id.in_((previous))).all()
      try:
          if category == 0:
              question = db.session.query(Question).filter(~Question.id.in_(previous_subquery)).order_by(func.random()).limit(1).one()
          else:
              question = db.session.query(Question).filter_by(category=category).filter(~Question.id.in_(previous_subquery)).order_by(func.random()).limit(1).one()
      except Exception as e:
          return jsonify(noquestion = "no more questions to load")

      return jsonify(question = question.format())

  @app.errorhandler(400)
  def error400(error):
      return jsonify({"success": False,"error": 400,"description": "Malformed Request"}), 400

  @app.errorhandler(404)
  def error404(error):
      return jsonify({"success": False,"error": 404,"description": "Requested endpoint is not found"}), 404

  @app.errorhandler(405)
  def error405(error):
      return jsonify({"success": False,"error": 405,"description": "Method not setup, please make sure that the HTTP method type is set correctly"}), 405

  @app.errorhandler(422)
  def error422(error):
    return jsonify({"success": False,"error": 422,"description": "Unprocessable due to origin restrictions"}), 422

  @app.errorhandler(500)
  def error500(error):
    return jsonify({"success": False,"error": 500,"description": "Server Error, please contact administrator"}), 500

  return app
