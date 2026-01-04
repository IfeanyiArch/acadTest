from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from assessment.models import Course, Submission
from assessment.tests.factories import (
    create_exam_with_questions,
    create_submission_with_answers,
)
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = "Seed the database with test data (users, courses, exams, questions, submissions)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--test-mode",
            action="store_true",
            help="Use smaller dataset for quick testing",
        )
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Flush the database before seeding (WARNING: deletes all data!)",
        )

    def handle(self, *args, **options):
        seeder = DatabaseSeeder(test_mode=options["test_mode"])

        if options["flush"]:
            seeder.flush_database()

        seeder.seed()


class DatabaseSeeder:
    """Database seeding utility"""

    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.created_items = {
            "users": 0,
            "courses": 0,
            "exams": 0,
            "questions": 0,
            "submissions": 0,
        }

    def flush_database(self):
        """Flush all data from database"""
        from django.core.management import call_command

        print("⚠️  Flushing database...")
        call_command("flush", "--noinput")
        print("✅ Database flushed")

    def create_users(self, count=10):
        """Create test users"""
        print(f"📝 Creating {count} users...")

        # Create admin user
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser(
                username="admin", email="admin@acadai.com", password="admin123"
            )
            print("  ✓ Created admin user (username: admin, password: admin123)")

        # Create regular users
        users = []
        for i in range(count):
            username = f"student{i + 1}"

            # Skip if user exists
            if User.objects.filter(username=username).exists():
                user = User.objects.get(username=username)
                users.append(user)
                continue

            user = User.objects.create_user(
                username=username,
                email=f"student{i + 1}@acadai.com",
                password="password123",
                first_name=f"Student{i + 1}",
                last_name="Test",
                user_type="STUDENT",
            )
            users.append(user)

        self.created_items["users"] = count + 1
        print(f"  ✓ Created {count} student users")
        return users

    def create_courses(self, count=5):
        """Create courses"""
        print(f"📚 Creating {count} courses...")

        course_data = [
            {"name": "Introduction to Computer Science", "code": "CS101"},
            {"name": "Data Structures and Algorithms", "code": "CS201"},
            {"name": "Database Systems", "code": "CS301"},
            {"name": "Web Development", "code": "CS302"},
            {"name": "Machine Learning", "code": "CS401"},
        ]

        courses = []
        for i in range(min(count, len(course_data))):
            # Skip if course exists
            if Course.objects.filter(code=course_data[i]["code"]).exists():
                course = Course.objects.get(code=course_data[i]["code"])
                courses.append(course)
                continue

            course = Course.objects.create(
                name=course_data[i]["name"],
                code=course_data[i]["code"],
                description=f"Learn about {course_data[i]['name'].lower()}",
            )
            courses.append(course)

        self.created_items["courses"] = len(courses)
        print(f"  ✓ Created {len(courses)} courses")
        return courses

    def create_exams_with_questions(self, courses, exams_per_course=2):
        """Create exams with questions for each course"""
        print("📋 Creating exams with questions...")

        exams = []
        total_questions = 0

        for course in courses:
            for i in range(exams_per_course):
                exam, questions = create_exam_with_questions(
                    num_mcq=3,
                    num_short=3,
                    num_long=2,
                    num_essay=1,
                    course=course,
                    title=f"{course.name} - Exam {i + 1}",
                )
                exams.append(exam)
                total_questions += len(questions)

        self.created_items["exams"] = len(exams)
        self.created_items["questions"] = total_questions
        print(f"  ✓ Created {len(exams)} exams")
        print(f"  ✓ Created {total_questions} questions")
        return exams

    def create_submissions(self, users, exams, submissions_per_user=3):
        """Create submissions for users"""
        print("✍️  Creating submissions...")

        submissions = []

        for user in users[:5]:  # Only first 5 users submit
            for exam in exams[:submissions_per_user]:
                # Check if submission already exists
                if Submission.objects.filter(student=user, exam=exam).exists():
                    continue

                # Create submission with answers
                submission, answers = create_submission_with_answers(
                    student=user, exam=exam
                )

                # Grade some submissions
                if len(submissions) % 2 == 0:
                    from assessment.services.grading_service import (
                        get_grading_service,
                    )

                    grading_service = get_grading_service("mock")

                    total_score = Decimal("0.00")
                    for answer in answers:
                        result = grading_service.grade_answer(
                            answer.question, answer.answer_text
                        )
                        answer.score = result["score"]
                        answer.feedback = result["feedback"]
                        answer.is_correct = result["is_correct"]
                        answer.grading_metadata = result["metadata"]
                        answer.save()
                        total_score += Decimal(str(result["score"]))

                    submission.total_score = total_score
                    submission.calculate_percentage()
                    submission.status = "GRADED"
                    submission.save()

                submissions.append(submission)

        self.created_items["submissions"] = len(submissions)
        print(f"  ✓ Created {len(submissions)} submissions")
        return submissions

    def seed(self):
        """Run the complete seeding process"""
        print("\n" + "=" * 60)
        print("🌱 Starting Database Seeding")
        print("=" * 60 + "\n")

        # Create users
        users = self.create_users(count=10 if not self.test_mode else 3)

        # Create courses
        courses = self.create_courses(count=5 if not self.test_mode else 2)

        # Create exams with questions
        exams = self.create_exams_with_questions(
            courses, exams_per_course=2 if not self.test_mode else 1
        )

        # Create submissions
        _ = self.create_submissions(
            users, exams, submissions_per_user=3 if not self.test_mode else 1
        )

        # Summary
        print("\n" + "=" * 60)
        print("✅ Seeding Complete!")
        print("=" * 60)
        print(f"  Users:       {self.created_items['users']}")
        print(f"  Courses:     {self.created_items['courses']}")
        print(f"  Exams:       {self.created_items['exams']}")
