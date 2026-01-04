from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from decimal import Decimal

from assessment.models import Submission, Answer
from .factories import (
    UserFactory,
    ActiveExamFactory,
    ExpiredExamFactory,
    FutureExamFactory,
    MCQQuestionFactory,
    SubmissionFactory,
    GradedSubmissionFactory,
    create_exam_with_questions,
    create_submission_with_answers,
)


class AuthenticationTest(TestCase):
    """Test cases for authentication"""

    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory(username="testuser", password="testpass123")

    def test_get_auth_token(self):
        """Test obtaining authentication token"""
        url = reverse("login")
        data = {"username": "testuser", "password": "testpass123"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

    def test_invalid_credentials(self):
        """Test authentication with invalid credentials"""
        url = reverse("login")
        data = {"username": "testuser", "password": "wrongpassword"}

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ExamAPITest(TestCase):
    """Test cases for Exam API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_list_exams_requires_authentication(self):
        """Test that listing exams requires authentication"""
        client = APIClient()  # No authentication
        url = reverse("exam-list")

        response = client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_active_exams(self):
        """Test listing active exams"""
        active_exam1 = ActiveExamFactory()
        active_exam2 = ActiveExamFactory()
        ExpiredExamFactory()  # Should not appear
        FutureExamFactory()  # Should not appear

        url = reverse("exam-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_list_exams_excludes_inactive(self):
        """Test that inactive exams are excluded"""
        ActiveExamFactory(is_active=False)

        url = reverse("exam-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    def test_retrieve_exam_details(self):
        """Test retrieving exam details with questions"""
        exam, questions = create_exam_with_questions(num_mcq=2, num_short=3)

        url = reverse("exam-detail", kwargs={"pk": exam.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], exam.id)
        self.assertEqual(response.data["title"], exam.title)
        self.assertEqual(len(response.data["questions"]), 5)
        self.assertEqual(response.data["question_count"], 5)

    def test_exam_details_exclude_expected_answers(self):
        """Test that expected answers are not exposed in exam details"""
        exam, questions = create_exam_with_questions(num_mcq=1)

        url = reverse("exam-detail", kwargs={"pk": exam.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for question_data in response.data["questions"]:
            self.assertNotIn("expected_answer", question_data)
            self.assertNotIn("grading_criteria", question_data)

    def test_check_exam_availability(self):
        """Test checking exam availability"""
        exam = ActiveExamFactory()

        url = reverse("exam-check-availability", kwargs={"pk": exam.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_available"])
        self.assertTrue(response.data["has_started"])
        self.assertFalse(response.data["has_ended"])
        self.assertFalse(response.data["already_submitted"])

    def test_check_exam_availability_with_existing_submission(self):
        """Test availability check when student has already submitted"""
        exam = ActiveExamFactory()
        SubmissionFactory(student=self.user, exam=exam)

        url = reverse("exam-check-availability", kwargs={"pk": exam.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["already_submitted"])


class SubmissionAPITest(TestCase):
    """Test cases for Submission API endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_create_submission_requires_authentication(self):
        """Test that creating submission requires authentication"""
        client = APIClient()  # No authentication
        url = reverse("submission-list")

        response = client.post(url, {})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_submission_successfully(self):
        """Test successful submission creation"""
        exam, questions = create_exam_with_questions(num_mcq=2, num_short=2)

        url = reverse("submission-list")
        data = {
            "exam_id": exam.id,
            "answers": [
                {"question_id": questions[0].id, "answer_text": "A"},
                {"question_id": questions[1].id, "answer_text": "B"},
                {"question_id": questions[2].id, "answer_text": "Short answer 1"},
                {"question_id": questions[3].id, "answer_text": "Short answer 2"},
            ],
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertEqual(response.data["status"], "GRADED")
        self.assertIsNotNone(response.data["total_score"])

    def test_create_submission_validates_exam_availability(self):
        """Test that submission validates exam availability"""
        exam = ExpiredExamFactory()
        questions = [MCQQuestionFactory(exam=exam)]

        url = reverse("submission-list")
        data = {
            "exam_id": exam.id,
            "answers": [{"question_id": questions[0].id, "answer_text": "A"}],
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("exam_id", response.data)

    def test_create_submission_prevents_duplicate(self):
        """Test that student cannot submit twice for same exam"""
        exam, questions = create_exam_with_questions(num_mcq=1)

        # First submission
        SubmissionFactory(student=self.user, exam=exam)

        # Attempt second submission
        url = reverse("submission-list")
        data = {
            "exam_id": exam.id,
            "answers": [{"question_id": questions[0].id, "answer_text": "A"}],
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_create_submission_validates_question_belongs_to_exam(self):
        """Test that questions belong to the specified exam"""
        exam1, questions1 = create_exam_with_questions(num_mcq=1)
        exam2, questions2 = create_exam_with_questions(num_mcq=1)

        url = reverse("submission-list")
        data = {
            "exam_id": exam1.id,
            "answers": [
                {"question_id": questions2[0].id, "answer_text": "A"}  # Wrong exam
            ],
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_submission_validates_no_duplicate_questions(self):
        """Test that same question cannot be answered twice"""
        exam, questions = create_exam_with_questions(num_mcq=2)

        url = reverse("submission-list")
        data = {
            "exam_id": exam.id,
            "answers": [
                {"question_id": questions[0].id, "answer_text": "A"},
                {"question_id": questions[0].id, "answer_text": "B"},  # Duplicate
            ],
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_submissions_for_current_user(self):
        """Test listing submissions for authenticated user only"""
        other_user = UserFactory()

        # Current user's submissions
        GradedSubmissionFactory(student=self.user)
        GradedSubmissionFactory(student=self.user)

        # Other user's submission (should not appear)
        GradedSubmissionFactory(student=other_user)

        url = reverse("submission-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_retrieve_submission_details(self):
        """Test retrieving detailed submission information"""
        submission, answers = create_submission_with_answers(student=self.user)

        url = reverse("submission-detail", kwargs={"pk": submission.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], submission.id)
        self.assertIn("answers", response.data)
        self.assertIn("exam", response.data)

    def test_cannot_retrieve_other_user_submission(self):
        """Test that users cannot access other users' submissions"""
        other_user = UserFactory()
        submission = GradedSubmissionFactory(student=other_user)

        url = reverse("submission-detail", kwargs={"pk": submission.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_filter_submissions_by_status(self):
        """Test filtering submissions by status"""
        GradedSubmissionFactory(student=self.user, status="GRADED")
        GradedSubmissionFactory(student=self.user, status="GRADED")
        SubmissionFactory(student=self.user, status="IN_PROGRESS")

        url = reverse("submission-my-submissions")
        response = self.client.get(url, {"status": "GRADED"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_filter_submissions_by_exam(self):
        """Test filtering submissions by exam"""
        exam1, _ = create_exam_with_questions()
        exam2, _ = create_exam_with_questions()

        GradedSubmissionFactory(student=self.user, exam=exam1)
        GradedSubmissionFactory(student=self.user, exam=exam2)
        GradedSubmissionFactory(student=self.user, exam=exam2)

        url = reverse("submission-my-submissions")
        response = self.client.get(url, {"exam_id": exam2.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_detailed_feedback_endpoint(self):
        """Test getting detailed feedback for submission"""
        submission, answers = create_submission_with_answers(student=self.user)

        url = reverse("submission-detailed-feedback", kwargs={"pk": submission.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("answers", response.data)

    def test_detailed_feedback_permission_check(self):
        """Test that detailed feedback is only accessible by submission owner"""
        other_user = UserFactory()
        submission = GradedSubmissionFactory(student=other_user)

        url = reverse("submission-detailed-feedback", kwargs={"pk": submission.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GradingIntegrationTest(TestCase):
    """Integration tests for the complete grading flow"""

    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_complete_submission_and_grading_flow(self):
        """Test complete flow from exam creation to graded submission"""
        # Create exam with questions
        exam, questions = create_exam_with_questions(num_mcq=2, num_short=2, num_long=1)

        # Submit answers
        url = reverse("submission-list")
        data = {
            "exam_id": exam.id,
            "answers": [
                {
                    "question_id": questions[0].id,
                    "answer_text": questions[0].expected_answer,
                },
                {"question_id": questions[1].id, "answer_text": "B"},
                {
                    "question_id": questions[2].id,
                    "answer_text": "This is a short answer",
                },
                {"question_id": questions[3].id, "answer_text": "Another short answer"},
                {
                    "question_id": questions[4].id,
                    "answer_text": "Long answer with details",
                },
            ],
        }

        response = self.client.post(url, data, format="json")

        # Verify submission was created and graded
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "GRADED")
        self.assertIsNotNone(response.data["total_score"])
        self.assertIsNotNone(response.data["percentage"])

        # Verify all answers were graded
        submission_id = response.data["id"]
        submission = Submission.objects.get(id=submission_id)

        self.assertEqual(submission.answers.count(), 5)
        for answer in submission.answers.all():
            self.assertIsNotNone(answer.score)
            self.assertIsNotNone(answer.is_correct)
            self.assertNotEqual(answer.feedback, "")

    def test_mcq_grading_accuracy(self):
        """Test that MCQ questions are graded accurately"""
        exam = ActiveExamFactory()
        question = MCQQuestionFactory(
            exam=exam, expected_answer="B", marks=Decimal("10.00")
        )

        # Submit correct answer
        url = reverse("submission-list")
        data = {
            "exam_id": exam.id,
            "answers": [{"question_id": question.id, "answer_text": "B"}],
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Check answer was graded correctly
        answer = Answer.objects.get(
            submission_id=response.data["id"], question=question
        )

        self.assertEqual(answer.score, Decimal("10.00"))
        self.assertTrue(answer.is_correct)
