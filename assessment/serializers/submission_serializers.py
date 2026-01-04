from rest_framework import serializers
from assessment.models import Exam, Question, Submission, Answer
from .exam_serializers import ExamDetailSerializer, QuestionSerializer


class AnswerSubmissionSerializer(serializers.Serializer):
    """
    Serializer for individual answer submission
    """

    question_id = serializers.IntegerField()
    answer_text = serializers.CharField(allow_blank=True)

    def validate_question_id(self, value):
        """Ensure question exists"""
        if not Question.objects.filter(id=value).exists():
            raise serializers.ValidationError("Invalid question ID")
        return value


class SubmissionCreateSerializer(serializers.Serializer):
    """
    Serializer for creating exam submissions
    """

    exam_id = serializers.IntegerField()
    answers = AnswerSubmissionSerializer(many=True)

    def validate_exam_id(self, value):
        """Validate exam exists and is available"""
        try:
            exam = Exam.objects.get(id=value)
        except Exam.DoesNotExist:
            raise serializers.ValidationError("Invalid exam ID")

        if not exam.is_available():
            raise serializers.ValidationError(
                "Exam is not currently available for submission"
            )

        return value

    def validate_answers(self, value):
        """Ensure at least one answer is provided"""
        if not value:
            raise serializers.ValidationError("At least one answer is required")
        return value

    def validate(self, data):
        """
        Cross-field validation

        """
        exam_id = data["exam_id"]
        answers = data["answers"]

        exam_questions = Question.objects.filter(exam_id=exam_id).values_list(
            "id", flat=True
        )
        submitted_question_ids = [ans["question_id"] for ans in answers]

        invalid_questions = set(submitted_question_ids) - set(exam_questions)
        if invalid_questions:
            raise serializers.ValidationError(
                f"Questions {invalid_questions} do not belong to this exam"
            )

        if len(submitted_question_ids) != len(set(submitted_question_ids)):
            raise serializers.ValidationError("Duplicate question submissions detected")

        return data


class AnswerSerializer(serializers.ModelSerializer):
    """
    Serializer for Answer model
    """

    question_text = serializers.CharField(
        source="question.question_text", read_only=True
    )
    question_order = serializers.IntegerField(source="question.order", read_only=True)
    question_type = serializers.CharField(
        source="question.question_type", read_only=True
    )
    max_marks = serializers.DecimalField(
        source="question.marks", max_digits=5, decimal_places=2, read_only=True
    )

    class Meta:
        model = Answer
        fields = [
            "id",
            "question",
            "question_text",
            "question_order",
            "question_type",
            "answer_text",
            "score",
            "max_marks",
            "feedback",
            "is_correct",
            "created_at",
        ]
        read_only_fields = ["id", "score", "feedback", "is_correct", "created_at"]


class SubmissionListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing submissions
    """

    exam_title = serializers.CharField(source="exam.title", read_only=True)
    course_name = serializers.CharField(source="exam.course.name", read_only=True)
    is_passed = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            "id",
            "exam",
            "exam_title",
            "course_name",
            "status",
            "started_at",
            "submitted_at",
            "total_score",
            "percentage",
            "is_passed",
        ]
        read_only_fields = fields

    def get_is_passed(self, obj):
        """Check if student passed the exam"""
        return obj.is_passed()


class SubmissionDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for submission detail view
    """

    exam = ExamDetailSerializer(read_only=True)
    answers = AnswerSerializer(many=True, read_only=True)
    is_passed = serializers.SerializerMethodField()
    student_username = serializers.CharField(source="student.username", read_only=True)
    student_email = serializers.CharField(source="student.email", read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "student",
            "student_username",
            "student_email",
            "exam",
            "status",
            "started_at",
            "submitted_at",
            "graded_at",
            "total_score",
            "percentage",
            "is_passed",
            "grading_feedback",
            "answers",
            "metadata",
        ]
        read_only_fields = fields

    def get_is_passed(self, obj):
        """Check if student passed the exam"""
        return obj.is_passed()


class AnswerDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed answer view
    """

    question = QuestionSerializer(read_only=True)
    grading_details = serializers.SerializerMethodField()

    class Meta:
        model = Answer
        fields = [
            "id",
            "question",
            "answer_text",
            "score",
            "feedback",
            "is_correct",
            "grading_metadata",
            "grading_details",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_grading_details(self, obj):
        """
        Format grading metadata for display
        """

        metadata = obj.grading_metadata
        if not metadata:
            return None

        return {
            "method": metadata.get("grading_method", "unknown"),
            "keyword_score": metadata.get("keyword_score"),
            "similarity_score": metadata.get("similarity_score"),
            "combined_score": metadata.get("combined_score"),
            "word_count": metadata.get("word_count"),
        }


class SubmissionStatsSerializer(serializers.Serializer):
    """
    Serializer for submission statistics
    """

    total_submissions = serializers.IntegerField()
    graded_submissions = serializers.IntegerField()
    passed_submissions = serializers.IntegerField()
    failed_submissions = serializers.IntegerField()
    average_score = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        fields = [
            "total_submissions",
            "graded_submissions",
            "passed_submissions",
            "failed_submissions",
            "average_score",
            "average_percentage",
        ]
