from django.contrib import admin
from assessment.models import Course, Submission, Exam, Answer, Question


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "created_at", "updated_at"]


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ["title", "is_active", "created_at", "updated_at"]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["question_type", "question_text", "created_at", "updated_at"]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ["answer_text", "score", "created_at", "updated_at"]


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ["student", "total_score", "percentage", "created_at", "updated_at"]
