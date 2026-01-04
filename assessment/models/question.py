from django.db import models
from django.core.validators import MinValueValidator


class Question(models.Model):
    """Represents a question in an exam"""

    QUESTION_TYPES = [
        ("MCQ", "Multiple Choice"),
        ("SHORT", "Short Answer"),
        ("LONG", "Long Answer"),
        ("ESSAY", "Essay"),
        ("TRUE_FALSE", "True/False"),
    ]

    exam = models.ForeignKey(
        "assessment.Exam", on_delete=models.CASCADE, related_name="questions"
    )
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    question_text = models.TextField()
    order = models.PositiveIntegerField(default=0)
    marks = models.DecimalField(
        max_digits=5, decimal_places=2, validators=[MinValueValidator(0)]
    )

    # For MCQ questions
    options = models.JSONField(
        default=dict,
        blank=True,
        help_text="For MCQ: {'A': 'option1', 'B': 'option2', ...}",
    )

    # Expected answer/solution
    expected_answer = models.TextField(help_text="Correct answer or reference solution")

    # Grading criteria
    grading_criteria = models.JSONField(
        default=dict, blank=True, help_text="Keywords, rubric, or grading parameters"
    )

    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "questions"
        ordering = ["exam", "order"]
        indexes = [
            models.Index(fields=["exam", "order"]),
            models.Index(fields=["question_type"]),
        ]

    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}..."
