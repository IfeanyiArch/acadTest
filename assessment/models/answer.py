from django.db import models
from django.core.validators import MinValueValidator


class Answer(models.Model):
    """Represents a student's answer to a specific question"""

    submission = models.ForeignKey(
        "assessment.Submission", on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(
        "assessment.Question", on_delete=models.CASCADE, related_name="answers"
    )
    answer_text = models.TextField()

    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    feedback = models.TextField(blank=True)
    is_correct = models.BooleanField(null=True, blank=True)

    grading_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Stores grading algorithm output, confidence scores, etc.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "answers"
        unique_together = ["submission", "question"]
        indexes = [
            models.Index(fields=["submission", "question"]),
            models.Index(fields=["question"]),
        ]

    def __str__(self):
        return f"Answer by {self.submission.student.username} to Q{self.question.order}"
