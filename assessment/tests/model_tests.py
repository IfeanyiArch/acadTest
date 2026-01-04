from django.test import TestCase
from decimal import Decimal

from .factories import (
    UserFactory,
    CourseFactory,
    ExamFactory,
    ActiveExamFactory,
    ExpiredExamFactory,
    FutureExamFactory,
    QuestionFactory,
    MCQQuestionFactory,
    SubmissionFactory,
    GradedSubmissionFactory,
    AnswerFactory,
    create_exam_with_questions,
)


class CourseModelTest(TestCase):
    """Test cases for Course model"""

    def test_course_creation(self):
        """Test creating a course"""
        course = CourseFactory(name="Data Structures", code="CS201")

        self.assertEqual(course.name, "Data Structures")
        self.assertEqual(course.code, "CS201")
        self.assertIsNotNone(course.created_at)

    def test_course_str_representation(self):
        """Test string representation"""
        course = CourseFactory(name="Algorithms", code="CS301")
        self.assertEqual(str(course), "CS301 - Algorithms")

    def test_course_unique_code(self):
        """Test that course code is unique"""
        CourseFactory(code="CS101")

        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            CourseFactory(code="CS101")


class ExamModelTest(TestCase):
    """Test cases for Exam model"""

    def test_exam_creation(self):
        """Test creating an exam"""
        course = CourseFactory()
        exam = ExamFactory(
            title="Midterm Exam",
            course=course,
            duration_minutes=90,
            total_marks=Decimal("100.00"),
        )

        self.assertEqual(exam.title, "Midterm Exam")
        self.assertEqual(exam.course, course)
        self.assertEqual(exam.duration_minutes, 90)
        self.assertEqual(exam.total_marks, Decimal("100.00"))

    def test_exam_is_available(self):
        """Test exam availability check"""
        active_exam = ActiveExamFactory()
        expired_exam = ExpiredExamFactory()
        future_exam = FutureExamFactory()

        self.assertTrue(active_exam.is_available())
        self.assertFalse(expired_exam.is_available())
        self.assertFalse(future_exam.is_available())

    def test_exam_has_started(self):
        """Test if exam has started"""
        active_exam = ActiveExamFactory()
        future_exam = FutureExamFactory()

        self.assertTrue(active_exam.has_started())
        self.assertFalse(future_exam.has_started())

    def test_exam_has_ended(self):
        """Test if exam has ended"""
        expired_exam = ExpiredExamFactory()
        active_exam = ActiveExamFactory()

        self.assertTrue(expired_exam.has_ended())
        self.assertFalse(active_exam.has_ended())

    def test_inactive_exam_not_available(self):
        """Test that inactive exams are not available"""
        exam = ActiveExamFactory(is_active=False)
        self.assertFalse(exam.is_available())


class QuestionModelTest(TestCase):
    """Test cases for Question model"""

    def test_question_creation(self):
        """Test creating a question"""
        exam = ExamFactory()
        question = QuestionFactory(
            exam=exam, question_type="SHORT", marks=Decimal("10.00")
        )

        self.assertEqual(question.exam, exam)
        self.assertEqual(question.question_type, "SHORT")
        self.assertEqual(question.marks, Decimal("10.00"))

    def test_mcq_question_with_options(self):
        """Test MCQ question with options"""
        question = MCQQuestionFactory()

        self.assertEqual(question.question_type, "MCQ")
        self.assertIn("A", question.options)
        self.assertIn("B", question.options)
        self.assertEqual(question.expected_answer, "B")

    def test_question_ordering(self):
        """Test question ordering within exam"""
        exam = ExamFactory()
        q1 = QuestionFactory(exam=exam, order=1)
        q2 = QuestionFactory(exam=exam, order=2)
        q3 = QuestionFactory(exam=exam, order=3)

        questions = list(exam.questions.all())
        self.assertEqual(questions[0], q1)
        self.assertEqual(questions[1], q2)
        self.assertEqual(questions[2], q3)


class SubmissionModelTest(TestCase):
    """Test cases for Submission model"""

    def test_submission_creation(self):
        """Test creating a submission"""
        student = UserFactory()
        exam = ExamFactory()
        submission = SubmissionFactory(student=student, exam=exam)

        self.assertEqual(submission.student, student)
        self.assertEqual(submission.exam, exam)
        self.assertEqual(submission.status, "IN_PROGRESS")
        self.assertIsNotNone(submission.started_at)

    def test_submission_unique_constraint(self):
        """Test that student can only submit once per exam"""
        student = UserFactory()
        exam = ExamFactory()
        SubmissionFactory(student=student, exam=exam)

        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            SubmissionFactory(student=student, exam=exam)

    def test_calculate_percentage(self):
        """Test percentage calculation"""
        exam = ExamFactory(total_marks=Decimal("100.00"))
        submission = GradedSubmissionFactory(exam=exam, total_score=Decimal("75.00"))

        percentage = submission.calculate_percentage()
        self.assertEqual(percentage, Decimal("75.00"))

    def test_is_passed(self):
        """Test pass/fail determination"""
        exam = ExamFactory(
            total_marks=Decimal("100.00"), passing_marks=Decimal("40.00")
        )

        passing_submission = GradedSubmissionFactory(
            exam=exam, total_score=Decimal("60.00")
        )

        failing_submission = GradedSubmissionFactory(
            exam=exam, total_score=Decimal("30.00")
        )

        self.assertTrue(passing_submission.is_passed())
        self.assertFalse(failing_submission.is_passed())

    def test_is_passed_returns_none_when_not_graded(self):
        """Test that is_passed returns None when not graded"""
        submission = SubmissionFactory()
        self.assertIsNone(submission.is_passed())


class AnswerModelTest(TestCase):
    """Test cases for Answer model"""

    def test_answer_creation(self):
        """Test creating an answer"""
        submission = SubmissionFactory()
        question = QuestionFactory(exam=submission.exam)
        answer = AnswerFactory(
            submission=submission, question=question, answer_text="This is my answer"
        )

        self.assertEqual(answer.submission, submission)
        self.assertEqual(answer.question, question)
        self.assertEqual(answer.answer_text, "This is my answer")
        self.assertIsNone(answer.score)

    def test_answer_unique_constraint(self):
        """Test that only one answer per question per submission"""
        submission = SubmissionFactory()
        question = QuestionFactory(exam=submission.exam)
        AnswerFactory(submission=submission, question=question)

        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            AnswerFactory(submission=submission, question=question)

    def test_answer_grading_fields(self):
        """Test answer grading fields"""
        answer = AnswerFactory(
            score=Decimal("8.50"),
            feedback="Good answer!",
            is_correct=True,
            grading_metadata={"method": "mock", "confidence": 0.85},
        )

        self.assertEqual(answer.score, Decimal("8.50"))
        self.assertEqual(answer.feedback, "Good answer!")
        self.assertTrue(answer.is_correct)
        self.assertEqual(answer.grading_metadata["method"], "mock")


class IntegrationTest(TestCase):
    """Integration tests for complete exam flow"""

    def test_complete_exam_with_questions(self):
        """Test creating a complete exam with multiple questions"""
        exam, questions = create_exam_with_questions(
            num_mcq=2, num_short=3, num_long=1, num_essay=1
        )

        self.assertEqual(exam.questions.count(), 7)
        self.assertEqual(exam.questions.filter(question_type="MCQ").count(), 2)
        self.assertEqual(exam.questions.filter(question_type="SHORT").count(), 3)

    def test_submission_with_all_answers(self):
        """Test creating submission with answers to all questions"""
        student = UserFactory()
        exam, questions = create_exam_with_questions(num_mcq=2, num_short=2)

        submission = SubmissionFactory(student=student, exam=exam)

        for question in questions:
            AnswerFactory(submission=submission, question=question)

        self.assertEqual(submission.answers.count(), 4)
        self.assertEqual(
            submission.answers.filter(question__question_type="MCQ").count(), 2
        )

    def test_graded_submission_has_all_scores(self):
        """Test that graded submission has scores for all answers"""
        exam, questions = create_exam_with_questions(num_mcq=2, num_short=2)
        submission = GradedSubmissionFactory(exam=exam)

        total_score = Decimal("0.00")
        for question in questions:
            answer = AnswerFactory(
                submission=submission,
                question=question,
                score=Decimal("7.50"),
                is_correct=True,
            )
            total_score += answer.score

        submission.total_score = total_score
        submission.calculate_percentage()
        submission.save()

        self.assertEqual(submission.answers.count(), 4)
        self.assertIsNotNone(submission.total_score)
        self.assertIsNotNone(submission.percentage)
