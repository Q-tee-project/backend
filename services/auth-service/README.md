# Auth Service

Authentication and class management service for the Q-tee platform.

## Features

### Authentication
- Teacher signup/login
- Student signup/login
- JWT token-based authentication
- Password hashing with bcrypt

### Class Management
- Teachers can create classrooms
- Automatic class code generation and Redis storage
- Students can request to join classes using class codes
- Teacher approval system for join requests
- Direct student registration by teachers

## API Endpoints

### Authentication
- `POST /api/auth/teacher/signup` - Teacher registration
- `POST /api/auth/teacher/login` - Teacher login
- `POST /api/auth/student/signup` - Student registration
- `POST /api/auth/student/login` - Student login
- `GET /api/auth/teacher/me` - Get teacher profile
- `GET /api/auth/student/me` - Get student profile

### Classrooms
- `POST /api/classrooms/create` - Create a classroom (teacher only)
- `GET /api/classrooms/my-classrooms` - Get teacher's classrooms
- `POST /api/classrooms/join-request` - Request to join class (student only)
- `GET /api/classrooms/join-requests/pending` - Get pending join requests (teacher only)
- `PUT /api/classrooms/join-requests/{id}/approve` - Approve/reject join request (teacher only)
- `POST /api/classrooms/{id}/students/register` - Directly register student (teacher only)
- `GET /api/classrooms/{id}/students` - Get classroom students (teacher only)

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `SECRET_KEY` - JWT secret key

## Running the Service

The service runs on port 8003 when deployed with docker-compose.

```bash
cd backend
docker-compose up auth-service
```

## Database Models

- **Teacher**: id, username, email, name, phone, hashed_password
- **Student**: id, username, email, name, phone, parent_phone, school_level, grade, hashed_password
- **ClassRoom**: id, name, school_level, grade, teacher_id, class_code
- **StudentJoinRequest**: id, student_id, classroom_id, status (pending/approved/rejected)