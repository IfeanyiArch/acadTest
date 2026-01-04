from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Prefetch
from core.pagination import StandardResultsSetPagination
from assessment.models import Exam, Question, Submission
from assessment.serializers import ExamListSerializer, ExamDetailSerializer


class ExamViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing exams.
    """

    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ExamDetailSerializer
        return ExamListSerializer

    def get_queryset(self):
        queryset = Exam.objects.filter(is_active=True).select_related("course")

        if self.action == "retrieve":
            # Prefetch questions for detail view
            queryset = queryset.prefetch_related(
                Prefetch("questions", queryset=Question.objects.order_by("order"))
            )

        return queryset.order_by("-start_time")

    @action(detail=True, methods=["get"])
    def check_availability(self, request, pk=None):
        """Check if exam is currently available for taking"""
        exam = self.get_object()

        # Check if student already has a submission
        existing_submission = Submission.objects.filter(
            student=request.user, exam=exam
        ).first()

        return Response(
            {
                "is_available": exam.is_available(),
                "has_started": exam.has_started(),
                "has_ended": exam.has_ended(),
                "already_submitted": existing_submission is not None,
                "submission_status": existing_submission.status
                if existing_submission
                else None,
            },
            status=status.HTTP_200_OK,
        )
