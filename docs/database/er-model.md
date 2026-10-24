# Modelo entidad-relación

```mermaid
erDiagram
    INSTITUTION ||--o{ USER : employs
    INSTITUTION ||--o{ CLASSROOM : has
    INSTITUTION ||--o{ ACADEMIC_PERIOD : defines
    INSTITUTION ||--|| RISK_THRESHOLD : configures
    CLASSROOM ||--o{ STUDENT : enrolls
    USER ||--o{ CLASSROOM : tutors
    CLASSROOM ||--o{ COURSE_ASSIGNMENT : has
    SUBJECT ||--o{ COURSE_ASSIGNMENT : "taught in"
    USER ||--o{ COURSE_ASSIGNMENT : teaches
    USER ||--o{ GUARDIANSHIP : "is guardian"
    STUDENT ||--o{ GUARDIANSHIP : "has guardian"
    STUDENT ||--o{ GRADE : receives
    SUBJECT ||--o{ GRADE : "graded in"
    ACADEMIC_PERIOD ||--o{ GRADE : "belongs to"
    STUDENT ||--o{ ATTENDANCE : records
    STUDENT ||--o{ BEHAVIOR_RECORD : has
    STUDENT ||--o{ FAMILY_SURVEY : "described by"
    STUDENT ||--o{ RISK_ASSESSMENT : evaluated
    ACADEMIC_PERIOD ||--o{ RISK_ASSESSMENT : "evaluated in"
    RISK_ASSESSMENT ||--o{ ALERT : triggers
    RISK_ASSESSMENT ||--o{ SUGGESTION : produces
    USER ||--o{ ALERT : receives
    STUDENT ||--o{ COMMITMENT : "agreed for"
    USER ||--o{ IMPORT_JOB : uploads

    INSTITUTION {
        bigint id PK
        varchar name
        varchar ugel
        varchar district
    }
    USER {
        bigint id PK
        bigint institution_id FK
        varchar email UK
        varchar password_hash
        varchar full_name
        enum role "DIRECTOR|TEACHER|PARENT|ANALYST"
        bool is_active
        datetime created_at
    }
    ACADEMIC_PERIOD {
        bigint id PK
        bigint institution_id FK
        smallint year
        tinyint bimester "1-4"
        date start_date
        date end_date
    }
    CLASSROOM {
        bigint id PK
        bigint institution_id FK
        bigint tutor_id FK
        smallint year
        tinyint grade "1-5"
        char section
    }
    SUBJECT {
        bigint id PK
        varchar name UK
    }
    COURSE_ASSIGNMENT {
        bigint id PK
        bigint classroom_id FK
        bigint subject_id FK
        bigint teacher_id FK
    }
    STUDENT {
        bigint id PK
        bigint institution_id FK
        bigint classroom_id FK
        varchar code UK
        varchar first_name
        varchar last_name
        date birth_date
        enum sex "M|F"
    }
    GUARDIANSHIP {
        bigint guardian_id PK, FK
        bigint student_id PK, FK
        varchar relationship
    }
    GRADE {
        bigint id PK
        bigint student_id FK
        bigint subject_id FK
        bigint period_id FK
        decimal score "0-20"
    }
    ATTENDANCE {
        bigint id PK
        bigint student_id FK
        date date
        enum status "PRESENT|ABSENT|LATE|JUSTIFIED"
    }
    BEHAVIOR_RECORD {
        bigint id PK
        bigint student_id FK
        bigint period_id FK
        tinyint rating "1-5"
        text notes
    }
    FAMILY_SURVEY {
        bigint id PK
        bigint student_id FK
        bigint period_id FK
        bigint responder_id FK
        tinyint study_hours_week
        enum parent_education "NONE|PRIMARY|SECONDARY|TECHNICAL|UNIVERSITY"
        bool home_internet
        bool has_study_device
        tinyint family_communication "1-5"
        bool student_works
        tinyint household_size
        datetime submitted_at
    }
    RISK_ASSESSMENT {
        bigint id PK
        bigint student_id FK
        bigint period_id FK
        decimal probability "0-1"
        enum level "LOW|MEDIUM|HIGH"
        varchar model_version
        json top_factors
        datetime created_at
    }
    SUGGESTION {
        bigint id PK
        bigint assessment_id FK
        enum audience "TEACHER|PARENT"
        varchar factor
        text content
    }
    ALERT {
        bigint id PK
        bigint assessment_id FK
        bigint recipient_id FK
        bool is_read
        datetime created_at
    }
    COMMITMENT {
        bigint id PK
        bigint student_id FK
        bigint tutor_id FK
        bigint guardian_id FK
        date meeting_date
        text agreements
        date follow_up_date
        enum status "OPEN|FULFILLED|BREACHED"
    }
    RISK_THRESHOLD {
        bigint institution_id PK, FK
        decimal medium_from "default 0.40"
        decimal high_from "default 0.70"
        bigint updated_by FK
        datetime updated_at
    }
    IMPORT_JOB {
        bigint id PK
        bigint uploaded_by FK
        enum kind "GRADES|ATTENDANCE|STUDENTS"
        varchar filename
        enum status "PENDING|DONE|FAILED"
        int rows_ok
        int rows_failed
        json errors
        datetime created_at
    }
```

## Notas

- Las notas usan la escala vigesimal (0 a 20) para que el modelo trabaje con valores numéricos.
- Restricciones únicas:
  - `GRADE(student_id, subject_id, period_id)`
  - `ATTENDANCE(student_id, date)`
  - `RISK_ASSESSMENT(student_id, period_id, model_version)`
- Los refresh tokens se guardan en una tabla técnica `refresh_token` (hash, expiración, revocado) que se omite del diagrama.
