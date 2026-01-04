from django.urls import path, include
from rest_framework.routers import DefaultRouter
from assessment.views.exam_views import ExamViewSet
from assessment.views.submission_views import SubmissionViewSet

router = DefaultRouter()


router.register(r"exams", ExamViewSet, basename="exam")
router.register(r"submissions", SubmissionViewSet, basename="submission")

urlpatterns = [
    path("v1", include(router.urls)),
]
