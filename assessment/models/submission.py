from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class Submission(models.Model):
    """Represents a student's exam submission"""

    STATUS_CHOICES = [
        ("IN_PROGRESS", "In Progress"),
        ("SUBMITTED", "Submitted"),
        ("GRADING", "Grading"),
        ("GRADED", "Graded"),
        ("FAILED", "Grading Failed"),
    ]

    student = models.ForeignKey(
        "authentication.User", on_delete=models.CASCADE, related_name="submissions"
    )
    exam = models.ForeignKey(
        "assessment.Exam", on_delete=models.CASCADE, related_name="submissions"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="IN_PROGRESS"
    )

    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)

    total_score = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )

    grading_feedback = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "submissions"
        ordering = ["-submitted_at"]
        unique_together = ["student", "exam"]
        indexes = [
            models.Index(fields=["student", "exam"]),
            models.Index(fields=["status", "submitted_at"]),
            models.Index(fields=["exam", "status"]),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.exam.title} ({self.status})"

    def calculate_percentage(self):
        """Calculate percentage score"""
        if self.total_score is not None and self.exam.total_marks > 0:
            self.percentage = (self.total_score / self.exam.total_marks) * 100
            return self.percentage
        return None

    def is_passed(self):
        """Check if student passed the exam"""
        if self.total_score is not None:
            return self.total_score >= self.exam.passing_marks
        return None
