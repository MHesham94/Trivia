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

    def testAllCategories(self):
        res = self.client().get('/api/categories')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(len(data))

    def testAllQuestions(self):
        res = self.client().get('/api/questions')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['total_questions'])
        self.assertTrue(len(data['questions']))
        self.assertTrue(len(data['categories']))

    def testQuestionPagination(self):
        res = self.client().get('/api/questions?page=1')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        page1Questions = data['questions']
        res = self.client().get('/api/questions?page=2')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        page2Questions = data['questions']

        self.assertNotEqual(page1Questions, page2Questions)

    def testCategoryQuestions(self):
        res = self.client().get('/api/categories/1/questions')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['current_category'])
        self.assertTrue(len(data['questions']))
        self.assertIsInstance(data['total_questions'], int)

    def testCategoryQuestionsFail(self):
        res = self.client().get('/api/categories/9999999/questions')
        data = json.loads(res.data)
        self.assertTrue(len(data['questions']) == 0)
        self.assertTrue(data['total_questions'] == 0)

    def testDeleteQuestion(self):
        newQuestion = Question('foo?','bar', 1, 1)
        db.session.add(newQuestion)
        db.session.commit()
        newQuestionId = newQuestion.id
        res = self.client().delete('/api/questions/{newQuestionId}')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['result'] == 'Deleted Sucessfully')

        count = db.session.query(Question).filter_by(id=newQuestionId).count()
        self.assertEqual(count, 0)


    def testAddQuestion(self):
        postData = '{"question":"foo","answer":"bar","difficulty":"3","category":2}'
        res = self.client().post('/api/questions', data=postData, headers={'Content-Type': 'application/json'})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['result']["question"] == 'foo')
        self.assertTrue(data['result']["answer"] == 'bar')
        self.assertEqual(data['result']["difficulty"], 3)
        self.assertEqual(data['result']["category"], 2)
        generatedId = data['result']["id"]
        count = db.session.query(Question).filter_by(id=generatedId).count()
        self.assertEqual(count, 1)

    def testSearchQuestion(self):
        db.session.query(Question).filter(Question.question.ilike('laba')).delete(synchronize_session='fetch')
        newQuestion = Question('barblabaf','foo', 1, 1)
        db.session.add(newQuestion)
        db.session.commit()

        postData = '{"searchTerm":"laba"}'
        res = self.client().post('/api/questions/search', data=postData, headers={'Content-Type': 'application/json'})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertNotEqual(data['total_questions'], 1)
        self.assertNotEqual(len(data['questions']), 1)

    def testQuiz(self):
        db.session.query(Category).filter(Category.type.like('Test')).delete(synchronize_session='fetch')
        newCategory = Category("Test")
        db.session.add(newCategory)
        db.session.commit()
        newCatId = str(newCategory.id)
        newQuestion = Question('foo?','bar', newCatId, 1)
        db.session.add(newQuestion)
        newQuestion2 = Question('foo2?','bar2', newCatId, 1)
        db.session.add(newQuestion2)
        db.session.commit()

        newQuestionId = str(newQuestion.id)
        newQuestion2Id = str(newQuestion2.id)

        postData = '{"previous_questions":[],"quiz_category":{"type":"Test","id":'+newCatId+'}}'
        res = self.client().post('/api/quizzes', data=postData, headers={'Content-Type': 'application/json'})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        firstReturnedQuestionId = str(data["question"]["id"])
        self.assertEqual(len(data), 1)

        postData = '{"previous_questions":['+firstReturnedQuestionId+'],"quiz_category":{"type":"Test","id":'+newCatId+'}}'
        res = self.client().post('/api/quizzes', data=postData, headers={'Content-Type': 'application/json'})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        secondReturnedQuestionId = str(data["question"]["id"])
        self.assertEqual(len(data), 1)

        self.assertNotEqual(firstReturnedQuestionId, secondReturnedQuestionId)

        postData = '{"previous_questions":['+firstReturnedQuestionId+','+secondReturnedQuestionId+'],"quiz_category":{"type":"Test","id":'+newCatId+'}}'
        res = self.client().post('/api/quizzes', data=postData, headers={'Content-Type': 'application/json'})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data["noquestion"])


    def testerror400(self):
        postData = '{"question":"Question?","answer":"Answer","difficulty":"3","category":1'
        res = self.client().post('/api/questions', data=postData, headers={'Content-Type': 'application/json'})
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 400)
        self.assertEqual(data["error"], 400)

    def testerror404(self):
        res = self.client().get('/api/foo')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data["error"], 404)

    def testerror405(self):
        res = self.client().put('/api/questions')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 405)
        self.assertEqual(data["error"], 405)

    def testerror500(self):
        res = self.client().get('/api/questions?page=-1')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 500)
        self.assertEqual(data["error"], 500)


# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()
