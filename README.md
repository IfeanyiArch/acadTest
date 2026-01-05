# Acad Test Application

This document provides instructions for setting up, running, seeding the database, and testing the Acad application.

## Getting Started

To run the application locally using Docker Compose, use the following command:

```bash
make local-run-build
```

This command will build the necessary Docker images, start the database and Redis services, and launch the Django application. The application will be accessible at `http://localhost:8000`.

## Database Seeding

To populate your database with initial data (e.g., for development or testing purposes), use the seed command:
**NOTE** this command needs to run after you build the project or when the exam time has expire and you need new test exam / data

```bash
make local-seed
```

This command will execute a custom Django management command to seed the database.

## API Documentation

For detailed information on the API endpoints, including request/response formats and authentication, please refer to the Postman documentation:

[Postman Documentation](https://documenter.getpostman.com/view/19877378/2sBXVcmYSX)
