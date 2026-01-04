from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Exam(models.Model):
    """Represents an exam/assessment"""

    title = models.CharField(max_length=255)
    course = models.ForeignKey(
        "assessment.Course", on_delete=models.CASCADE, related_name="exams"
    )
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(
        help_text="Duration in minutes", validators=[MinValueValidator(1)]
    )
    total_marks = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=100.00,
        validators=[MinValueValidator(0)],
    )
    passing_marks = models.DecimalField(
        max_digits=6, decimal_places=2, default=40.00, validators=[MinValueValidator(0)]
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    instructions = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "exams"
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["course", "is_active"]),
            models.Index(fields=["start_time", "end_time"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.course.code}"

    def is_available(self):
        """Check if exam is currently available"""
        now = timezone.now()
        return self.is_active and self.start_time <= now <= self.end_time

    def has_started(self):
        """Check if exam has started"""
        return timezone.now() >= self.start_time

    def has_ended(self):
        """Check if exam has ended"""
        return timezone.now() > self.end_time
