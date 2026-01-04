from rest_framework import serializers
from assessment.models import Course, Exam, Question


class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer for Course model
    """

    class Meta:
        model = Course
        fields = ["id", "name", "code", "description", "created_at"]
        read_only_fields = ["id", "created_at"]


class QuestionSerializer(serializers.ModelSerializer):
    """
    Serializer for Question model
    """

    class Meta:
        model = Question
        fields = [
            "id",
            "question_type",
            "question_text",
            "order",
            "marks",
            "options",
            "metadata",
        ]
        read_only_fields = ["id"]


class ExamListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing exams
    """

    course_name = serializers.CharField(source="course.name", read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = [
            "id",
            "title",
            "course",
            "course_name",
            "course_code",
            "duration_minutes",
            "total_marks",
            "start_time",
            "end_time",
            "is_available",
            "description",
        ]
        read_only_fields = ["id"]

    def get_is_available(self, obj):
        """
        Check if exam is currently available
        """

        return obj.is_available()


class ExamDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for exam detail view

    """

    course = CourseSerializer(read_only=True)
    questions = QuestionSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = [
            "id",
            "title",
            "course",
            "description",
            "duration_minutes",
            "total_marks",
            "passing_marks",
            "start_time",
            "end_time",
            "instructions",
            "questions",
            "question_count",
            "metadata",
        ]
        read_only_fields = ["id"]

    def get_question_count(self, obj):
        """Return total number of questions in exam"""
        return obj.questions.count()
