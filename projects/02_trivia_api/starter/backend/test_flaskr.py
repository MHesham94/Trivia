import os
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category, db


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""
    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client
        self.database_name = "trivia_test"
        self.database_path = "postgres://{}/{}".format('localhost:5432', self.database_name)
        setup_db(self.app, self.database_path)

        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()

    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """

    def All_Categories(self):
        path = self.client().get('/api/categories')
        message = json.loads(path.message)
        self.assertEqual(path.status_code, 200)
        self.assertTrue(len(message))

    def All_Question(self):
        path = self.client().get('/api/Question')
        message = json.loads(path.message)
        self.assertEqual(path.status_code, 200)
        self.assertTrue(message['total_Question'])
        self.assertTrue(len(message['Question']))
        self.assertTrue(len(message['categories']))


    def Category_Question(self):
        path = self.client().get('/api/categories/1/Question')
        message = json.loads(path.message)
        self.assertEqual(path.status_code, 200)
        self.assertTrue(message['current_category'])
        self.assertTrue(len(message['Question']))
        self.assertIsInstance(message['total_Question'], int)



    def Delete_Question(self):
        newQuestion = Question('are you here?','yes', 1, 1)
        db.session.add(newQuestion)
        db.session.commit()
        newQuestionId = newQuestion.id
        path = self.client().delete('/api/Question/{newQuestionId}')
        message = json.loads(path.message)
        self.assertEqual(path.status_code, 200)
        self.assertTrue(message['result'] == 'Deleted Sucessfully')
        count = db.session.quey(Question).filter_by(id=newQuestionId).count()
        self.assertEqual(count, 0)

    def Question_Scroll(self):
        path = self.client().get('/api/Question?page=1')
        message = json.loads(path.message)
        self.assertEqual(path.status_code, 200)
        Question1 = message['Question']
        path = self.client().get('/api/Question?page=2')
        message = json.loads(path.message)
        self.assertEqual(path.status_code, 200)
        Question2 = message['Question']
        self.assertNotEqual(Question1, Question2)



    def Add_Question(self):
        postData = '{"question":"how difficult is it","answer":"no idea","difficulty":"3","category":2}'
        path = self.client().post('/api/Question', message=postData, headers={'Content-Type': 'application/json'})
        message = json.loads(path.message)
        self.assertEqual(path.status_code, 200)
        self.assertTrue(message['result']["question"] == 'how difficult is it')
        self.assertTrue(message['result']["answer"] == 'no idea')
        self.assertEqual(message['result']["difficulty"], 3)
        self.assertEqual(message['result']["category"], 2)
        generatedId = message['result']["id"]
        count = db.session.query(Question).filter_by(id=generatedId).count()
        self.assertEqual(count, 1)

    def Search_Question(self):
        db.session.query(Question).filter(Question.question.ilike('laba')).delete(synchronize_session='fetch')
        newQuestion = Question('no idea','how difficult is it', 1, 1)
        db.session.add(newQuestion)
        db.session.commit()
        postData = '{"searchTerm":"here"}'
        path = self.client().post('/api/Question/search', message=postData, headers={'Content-Type': 'application/json'})
        message = json.loads(path.message)
        self.assertEqual(path.status_code, 200)
        self.assertNotEqual(message['total_Question'], 1)
        self.assertNotEqual(len(message['Question']), 1)

    def testQuiz(self):
        db.session.query(Category).filter(Category.type.like('Trivia')).delete(synchronize_session='fetch')
        db.session.add(newCategory)
        newCategory = Category("Trivia")
        newCatId = str(newCategory.id)
        newQuestionId = str(newQuestion.id)
        newQuestion2Id = str(newQuestion2.id)
        newQuestion = Question('how many moon do we have?','zero', newCatId, 1)
        newQuestion2 = Question('how many suns are in the solar system?','None', newCatId, 1)
        db.session.add(newQuestion)
        db.session.add(newQuestion2)
        db.session.commit()
        postData = '{"previous_Question":[],"quiz_category":{"type":"Test","id":'+newCatId+'}}'
        path = self.client().post('/api/quizzes')
        message = json.loads(path.message)
        self.assertEqual(path.status_code, 200)
        first_QuestionId = str(message["question"]["id"])
        self.assertEqual(len(message), 1)
        postData = '{"previous_Question":['+firstReturnedQuestionId+'],"quiz_category":{"type":"Test","id":'+newCatId+'}}'
        path = self.client().post('/api/quizzes')
        message = json.loads(path.message)
        self.assertEqual(path.status_code, 200)
        second_QuestionId = str(message["question"]["id"])
        self.assertEqual(len(message), 1)
        self.assertNotEqual(first_uestionId, second_QuestionId)
        postData = '{"previous_Question":['+first_QuestionId+','+second_QuestionId+'],"quiz_category":{"type":"Trivia","id":'+newCatId+'}}'
        path = self.client().post('/api/quizzes')
        message = json.loads(path.message)
        self.assertEqual(path.status_code, 200)
        self.assertTrue(message["None"])

    def error500(self):
        path = self.client().get('/api/Question?page=-1')
        message = json.loads(path.message)
        self.assertEqual(path.status_code, 500)
        self.assertEqual(message["error"], 500)
	
    def error400(self):
        postData = '{"question":"Question?","answer":"Answer","difficulty":"3","category":1'
        path = self.client().post('/api/Question', message=postData, headers={'Content-Type': 'application/json'})
        message = json.loads(path.message)
        self.assertEqual(path.status_code, 400)
        self.assertEqual(message["error"], 400)

    def error404(self):
        path = self.client().get('/api/test')
        message = json.loads(path.message)
        self.assertEqual(path.status_code, 404)
        self.assertEqual(message["error"], 404)

    def error405(self):
        path = self.client().put('/api/Question')
        message = json.loads(path.message)
        self.assertEqual(path.status_code, 405)
        self.assertEqual(message["error"], 405)



# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
