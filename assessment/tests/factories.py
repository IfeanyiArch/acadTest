import factory
from factory.django import DjangoModelFactory
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import Course, Exam, Question, Submission, Answer


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"student{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.set_password(extracted)
        else:
            self.set_password("testpass123")


class CourseFactory(DjangoModelFactory):
    class Meta:
        model = Course

    name = factory.Faker("catch_phrase")
    code = factory.Sequence(lambda n: f"CS{100 + n}")
    description = factory.Faker("text", max_nb_chars=200)


class ExamFactory(DjangoModelFactory):
    class Meta:
        model = Exam

    title = factory.Faker("sentence", nb_words=4)
    course = factory.SubFactory(CourseFactory)
    description = factory.Faker("paragraph")
    duration_minutes = 60
    total_marks = Decimal("100.00")
    passing_marks = Decimal("40.00")
    start_time = factory.LazyFunction(lambda: timezone.now() - timedelta(hours=1))
    end_time = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=2))
    is_active = True
    instructions = factory.Faker("text", max_nb_chars=300)
    metadata = factory.Dict({"difficulty": "medium", "type": "midterm"})


class ActiveExamFactory(ExamFactory):
    """Factory for currently active exams"""

    start_time = factory.LazyFunction(lambda: timezone.now() - timedelta(hours=1))
    end_time = factory.LazyFunction(lambda: timezone.now() + timedelta(hours=2))
    is_active = True


class ExpiredExamFactory(ExamFactory):
    """Factory for expired exams"""

    start_time = factory.LazyFunction(lambda: timezone.now() - timedelta(days=2))
    end_time = factory.LazyFunction(lambda: timezone.now() - timedelta(days=1))
    is_active = True


class FutureExamFactory(ExamFactory):
    """Factory for future exams"""

    start_time = factory.LazyFunction(lambda: timezone.now() + timedelta(days=1))
    end_time = factory.LazyFunction(lambda: timezone.now() + timedelta(days=2))
    is_active = True


class QuestionFactory(DjangoModelFactory):
    class Meta:
        model = Question

    exam = factory.SubFactory(ExamFactory)
    question_type = "SHORT"
    question_text = factory.Faker("sentence", nb_words=10)
    order = factory.Sequence(lambda n: n + 1)
    marks = Decimal("10.00")
    options = factory.Dict({})
    expected_answer = factory.Faker("paragraph", nb_sentences=3)
    grading_criteria = factory.Dict(
        {"keywords": ["algorithm", "data structure", "complexity"]}
    )
    metadata = factory.Dict({})


class MCQQuestionFactory(QuestionFactory):
    """Factory for Multiple Choice Questions"""

    question_type = "MCQ"
    options = factory.Dict(
        {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}
    )
    expected_answer = "B"
    grading_criteria = factory.Dict({})


class ShortAnswerQuestionFactory(QuestionFactory):
    """Factory for Short Answer Questions"""

    question_type = "SHORT"
    options = factory.Dict({})
    expected_answer = factory.Faker("sentence", nb_words=15)
    grading_criteria = factory.Dict({"keywords": ["key1", "key2", "key3"]})


class LongAnswerQuestionFactory(QuestionFactory):
    """Factory for Long Answer Questions"""

    question_type = "LONG"
    marks = Decimal("20.00")
    options = factory.Dict({})
    expected_answer = factory.Faker("paragraph", nb_sentences=10)
    grading_criteria = factory.Dict(
        {"keywords": ["concept1", "concept2", "concept3", "example", "explanation"]}
    )


class EssayQuestionFactory(QuestionFactory):
    """Factory for Essay Questions"""

    question_type = "ESSAY"
    marks = Decimal("30.00")
    options = factory.Dict({})
    expected_answer = factory.Faker("paragraph", nb_sentences=15)
    grading_criteria = factory.Dict(
        {"keywords": ["thesis", "argument", "evidence", "conclusion", "analysis"]}
    )


class SubmissionFactory(DjangoModelFactory):
    class Meta:
        model = Submission

    student = factory.SubFactory(UserFactory)
    exam = factory.SubFactory(ExamFactory)
    status = "IN_PROGRESS"
    started_at = factory.LazyFunction(timezone.now)
    submitted_at = None
    graded_at = None
    total_score = None
    percentage = None
    grading_feedback = ""
    metadata = factory.Dict({})


class SubmittedSubmissionFactory(SubmissionFactory):
    """Factory for submitted but not graded submissions"""

    status = "SUBMITTED"
    submitted_at = factory.LazyFunction(timezone.now)


class GradedSubmissionFactory(SubmissionFactory):
    """Factory for graded submissions"""

    status = "GRADED"
    submitted_at = factory.LazyFunction(lambda: timezone.now() - timedelta(minutes=30))
    graded_at = factory.LazyFunction(lambda: timezone.now() - timedelta(minutes=15))
    total_score = Decimal("75.00")
    percentage = Decimal("75.00")
    grading_feedback = "Good job! You passed the exam."


class AnswerFactory(DjangoModelFactory):
    class Meta:
        model = Answer

    submission = factory.SubFactory(SubmissionFactory)
    question = factory.SubFactory(QuestionFactory)
    answer_text = factory.Faker("paragraph", nb_sentences=3)
    score = None
    feedback = ""
    is_correct = None
    grading_metadata = factory.Dict({})


class GradedAnswerFactory(AnswerFactory):
    """Factory for graded answers"""

    score = Decimal("8.00")
    feedback = "Good answer!"
    is_correct = True
    grading_metadata = factory.Dict(
        {"grading_method": "mock", "similarity_score": 0.85}
    )


# Helper function to create a complete exam with questions
def create_exam_with_questions(
    num_mcq=2, num_short=3, num_long=2, num_essay=1, **exam_kwargs
):
    """Create an exam with multiple questions of different types"""
    exam = ExamFactory(**exam_kwargs)

    questions = []
    order = 1

    # Create MCQ questions
    for _ in range(num_mcq):
        questions.append(
            MCQQuestionFactory(exam=exam, order=order, marks=Decimal("5.00"))
        )
        order += 1

    # Create short answer questions
    for _ in range(num_short):
        questions.append(
            ShortAnswerQuestionFactory(exam=exam, order=order, marks=Decimal("10.00"))
        )
        order += 1

    # Create long answer questions
    for _ in range(num_long):
        questions.append(
            LongAnswerQuestionFactory(exam=exam, order=order, marks=Decimal("20.00"))
        )
        order += 1

    # Create essay questions
    for _ in range(num_essay):
        questions.append(
            EssayQuestionFactory(exam=exam, order=order, marks=Decimal("30.00"))
        )
        order += 1

    # Update exam total marks
    total = sum(q.marks for q in questions)
    exam.total_marks = total
    exam.save()

    return exam, questions


# Helper function to create a submission with answers
def create_submission_with_answers(student=None, exam=None, answer_texts=None):
    """Create a submission with answers for all questions in an exam"""
    if not student:
        student = UserFactory()

    if not exam:
        exam, questions = create_exam_with_questions()
    else:
        questions = list(exam.questions.all())

    submission = SubmittedSubmissionFactory(student=student, exam=exam)

    answers = []
    for i, question in enumerate(questions):
        answer_text = (
            answer_texts[i]
            if answer_texts and i < len(answer_texts)
            else f"Answer to question {i + 1}"
        )
        answer = AnswerFactory(
            submission=submission, question=question, answer_text=answer_text
        )
        answers.append(answer)

    return submission, answers
