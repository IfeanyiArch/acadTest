from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
from django.db.models import Prefetch
from core.pagination import StandardResultsSetPagination
from assessment.models import Exam, Question, Submission, Answer
from assessment.serializers import (
    SubmissionCreateSerializer,
    SubmissionListSerializer,
    SubmissionDetailSerializer,
)
from assessment.services.grading_service import get_grading_service


class SubmissionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing exam submissions.

    """

    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    http_method_names = ["get", "post"]

    def get_serializer_class(self):
        if self.action == "create":
            return SubmissionCreateSerializer
        elif self.action == "retrieve":
            return SubmissionDetailSerializer
        return SubmissionListSerializer

    def get_queryset(self):
        """
        Only return submissions for the authenticated user
        Optimize queries with select_related and prefetch_related
        """
        user = self.request.user

        queryset = Submission.objects.filter(student=user).select_related(
            "exam", "exam__course"
        )

        if self.action == "retrieve":
            # Prefetch answers with questions for detail view
            queryset = queryset.prefetch_related(
                Prefetch(
                    "answers",
                    queryset=Answer.objects.select_related("question").order_by(
                        "question__order"
                    ),
                ),
                "exam__questions",
            )

        return queryset.order_by("-submitted_at")

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
        Submit exam answers securely
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        exam_id = serializer.validated_data["exam_id"]
        answers_data = serializer.validated_data["answers"]

        exam = get_object_or_404(Exam, id=exam_id)

        # Check if student already submitted
        existing_submission = Submission.objects.filter(
            student=request.user, exam=exam
        ).first()

        if existing_submission:
            return Response(
                {"error": "You have already submitted this exam"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        submission = Submission.objects.create(
            student=request.user,
            exam=exam,
            status="SUBMITTED",
            submitted_at=timezone.now(),
        )

        answers = []
        for answer_data in answers_data:
            question = Question.objects.get(id=answer_data["question_id"])
            answer = Answer.objects.create(
                submission=submission,
                question=question,
                answer_text=answer_data["answer_text"],
            )
            answers.append(answer)

        # Initiate grading
        try:
            self._grade_submission(submission, answers)
        except Exception as e:
            submission.status = "FAILED"
            submission.grading_feedback = f"Grading error: {str(e)}"
            submission.save()

        # Return detailed submission
        submission.refresh_from_db()
        result_serializer = SubmissionDetailSerializer(submission)

        return Response(result_serializer.data, status=status.HTTP_201_CREATED)

    def _grade_submission(self, submission, answers):
        """Grade submission using grading service"""
        submission.status = "GRADING"
        submission.save()

        grading_service = get_grading_service("mock")

        total_score = 0.0

        for answer in answers:
            # Grade each answer
            grading_result = grading_service.grade_answer(
                answer.question, answer.answer_text
            )

            # Update answer with grading results
            answer.score = grading_result["score"]
            answer.feedback = grading_result["feedback"]
            answer.is_correct = grading_result["is_correct"]
            answer.grading_metadata = grading_result["metadata"]
            answer.save()

            total_score += grading_result["score"]

        # Update submission with final score
        submission.total_score = total_score
        submission.calculate_percentage()
        submission.status = "GRADED"
        submission.graded_at = timezone.now()

        # Generate overall feedback
        if submission.is_passed():
            submission.grading_feedback = (
                f"Congratulations! You passed with {submission.percentage:.2f}%"
            )
        else:
            submission.grading_feedback = (
                f"You scored {submission.percentage:.2f}%. Keep practicing!"
            )

        submission.save()

    @action(detail=False, methods=["get"])
    def my_submissions(self, request):
        """Get all submissions for the current user with filtering options"""
        queryset = self.get_queryset()

        status_param = request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        exam_id = request.query_params.get("exam_id")
        if exam_id:
            queryset = queryset.filter(exam_id=exam_id)

        course_id = request.query_params.get("course_id")
        if course_id:
            queryset = queryset.filter(exam__course_id=course_id)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def detailed_feedback(self, request, pk=None):
        """Get detailed feedback for a specific submission"""
        submission = self.get_object()

        # Ensure the submission belongs to the requesting user
        if submission.student != request.user:
            return Response(
                {"error": "You do not have permission to view this submission"},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = SubmissionDetailSerializer(submission)
        return Response(serializer.data)
