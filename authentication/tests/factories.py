import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from .models import UserProfile

User = get_user_model()


class UserFactory(DjangoModelFactory):
    """Factory for creating User instances"""

    class Meta:
        model = User
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True
    is_staff = False
    is_superuser = False
    user_type = "STUDENT"

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        """Set password for user"""
        if not create:
            return

        if extracted:
            self.set_password(extracted)
        else:
            self.set_password("password123")

    @factory.post_generation
    def profile(self, create, extracted, **kwargs):
        """Create user profile"""
        if not create:
            return

        UserProfileFactory(user=self)


class UserProfileFactory(DjangoModelFactory):
    """Factory for creating UserProfile instances"""

    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    student_id = factory.Sequence(lambda n: f"STU{n:06d}")
    enrollment_year = 2024
    major = factory.Faker("job")
    timezone = "UTC"
    notification_preferences = factory.Dict(
        {"email_notifications": True, "sms_notifications": False}
    )


class TokenFactory(DjangoModelFactory):
    """Factory for creating authentication tokens"""

    class Meta:
        model = Token

    user = factory.SubFactory(UserFactory)


class StudentFactory(UserFactory):
    """Factory for creating Student users"""

    user_type = "STUDENT"


class InstructorFactory(UserFactory):
    """Factory for creating Instructor users"""

    user_type = "INSTRUCTOR"
    is_staff = True


class AdminUserFactory(UserFactory):
    """Factory for creating Admin users"""

    user_type = "ADMIN"
    is_staff = True
    is_superuser = True
