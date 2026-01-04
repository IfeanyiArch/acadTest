from django.db import models


class UserProfile(models.Model):
    """
    Additional profile information for users
    """

    user = models.OneToOneField(
        "authentication.User", on_delete=models.CASCADE, related_name="profile"
    )

    student_id = models.CharField(max_length=50, blank=True, unique=True, null=True)
    enrollment_year = models.IntegerField(blank=True, null=True)
    major = models.CharField(max_length=100, blank=True)

    notification_preferences = models.JSONField(default=dict, blank=True)
    timezone = models.CharField(max_length=50, default="UTC")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_profiles"

    def __str__(self):
        return f"Profile: {self.user.username}"
