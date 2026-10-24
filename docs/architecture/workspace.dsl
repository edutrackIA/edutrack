workspace "EduTrack" "Seguimiento académico y alerta temprana del riesgo de desaprobación y deserción escolar." {

    !identifiers hierarchical

    model {
        director = person "Director" "Supervisa los indicadores de riesgo de la institución y emite reportes oficiales."
        teacher = person "Docente / Tutor" "Registra notas y conducta de sus aulas y atiende las alertas de sus estudiantes."
        parent = person "Padre de familia" "Consulta el progreso de su hijo, responde encuestas sociofamiliares y sigue pautas de apoyo."
        analyst = person "Analista" "Importa datos masivos, ejecuta el modelo predictivo y calibra los umbrales de riesgo."

        email = softwareSystem "Servicio de correo" "Entrega notificaciones por correo electrónico (Amazon SES / SMTP)." "External"

        edutrack = softwareSystem "EduTrack" "Plataforma web que estima el riesgo de desaprobación y deserción escolar con Machine Learning." {

            spa = container "Single-Page App" "Interfaz por rol: dashboards con semáforos, fichas, encuestas y alertas." "React, Vite, TypeScript" "Web Browser"
            proxy = container "Servidor web" "Entrega los archivos de la SPA y enruta /api/v1 hacia la API principal." "Nginx" "Proxy"

            api = container "API principal" "Autenticación, RBAC, dominio académico, ingesta, orquestación del riesgo, alertas y reportes." "Python, FastAPI" {
                security = component "Seguridad" "Login, emisión y rotación de JWT, verificación de rol y pertenencia." "FastAPI router + dependencies, bcrypt"
                academic = component "Módulo académico" "Estudiantes, aulas, notas, asistencia, conducta y encuestas sociofamiliares." "FastAPI router"
                imports = component "Módulo de importación" "Valida y carga archivos CSV/Excel con reporte de errores por fila." "FastAPI router, pandas"
                risk = component "Orquestador de riesgo" "Construye el vector de características, invoca al servicio ML y asigna el nivel según umbrales." "Service"
                mlClient = component "Cliente ML" "Llamadas HTTP con timeout y reintentos al servicio ML." "httpx"
                alerts = component "Alertas y sugerencias" "Genera pautas pedagógicas por factor y notifica a tutores y padres." "Service"
                reporting = component "Dashboard y reportes" "Agrega indicadores por aula e institución y genera reportes PDF." "FastAPI router, WeasyPrint"
                settings = component "Configuración" "Gestiona los umbrales de riesgo por institución." "FastAPI router"
                repositories = component "Repositorios" "Acceso a datos y transacciones." "SQLAlchemy 2"
            }

            ml = container "Servicio ML" "Inferencia del riesgo y explicación por factores. Sin estado ni acceso a la base de datos." "Python, FastAPI, scikit-learn" {
                router = component "Endpoints de predicción" "Expone /v1/predict, /v1/predict/batch y /v1/model." "FastAPI router"
                validator = component "Validador de características" "Valida tipos, rangos y categorías del vector de entrada." "Pydantic"
                predictor = component "Predictor" "Calcula la probabilidad de riesgo con el modelo Random Forest." "scikit-learn"
                explainer = component "Explicador" "Obtiene los factores con mayor contribución a cada predicción." "scikit-learn"
                loader = component "Cargador de modelo" "Carga y mantiene en memoria el modelo versionado y sus metadatos." "joblib"
            }

            training = container "Pipeline de entrenamiento" "Genera el dataset sintético, aplica VIF y SMOTE, entrena y evalúa el Random Forest y publica el modelo." "Python, scikit-learn, imbalanced-learn" "Batch"
            modelStore = container "Repositorio de modelos" "Artefactos .joblib versionados con métricas y lista de características." "Volumen Docker / Amazon S3" "Storage"
            db = container "Base de datos" "Datos académicos, sociofamiliares, evaluaciones de riesgo, alertas y usuarios." "MySQL 8" "Database"
        }

        # Contexto
        director -> edutrack "Consulta indicadores de riesgo y exporta reportes"
        teacher -> edutrack "Registra notas y conducta, atiende alertas y registra compromisos"
        parent -> edutrack "Consulta el progreso de su hijo y responde encuestas"
        analyst -> edutrack "Importa datos, ejecuta evaluaciones y ajusta umbrales"
        email -> teacher "Envía alertas de riesgo"
        email -> parent "Envía avisos y pautas de apoyo"

        # Contenedores
        director -> edutrack.spa "Usa" "HTTPS"
        teacher -> edutrack.spa "Usa" "HTTPS"
        parent -> edutrack.spa "Usa" "HTTPS"
        analyst -> edutrack.spa "Usa" "HTTPS"
        edutrack.proxy -> edutrack.spa "Entrega los archivos estáticos" "HTTPS"
        edutrack.spa -> edutrack.api "Llama a la API a través del servidor web" "JSON/HTTPS, JWT"
        edutrack.proxy -> edutrack.api "Enruta /api/v1" "HTTP"
        edutrack.api -> edutrack.db "Lee y escribe" "SQL/TCP"
        edutrack.api -> edutrack.ml "Solicita predicciones" "JSON/HTTP"
        edutrack.api -> email "Envía notificaciones" "SMTP"
        edutrack.ml -> edutrack.modelStore "Carga el modelo al iniciar"
        edutrack.training -> edutrack.modelStore "Publica el modelo versionado"

        # Componentes de la API
        edutrack.spa -> edutrack.api.security "Inicia sesión y renueva tokens" "JSON/HTTPS"
        edutrack.spa -> edutrack.api.academic "Gestiona fichas y encuestas" "JSON/HTTPS"
        edutrack.spa -> edutrack.api.imports "Sube archivos" "multipart/HTTPS"
        edutrack.spa -> edutrack.api.risk "Ejecuta evaluaciones" "JSON/HTTPS"
        edutrack.spa -> edutrack.api.alerts "Consulta alertas" "JSON/HTTPS"
        edutrack.spa -> edutrack.api.reporting "Consulta dashboard y PDF" "JSON/HTTPS"
        edutrack.spa -> edutrack.api.settings "Ajusta umbrales" "JSON/HTTPS"

        edutrack.api.academic -> edutrack.api.security "Verifica permisos"
        edutrack.api.imports -> edutrack.api.security "Verifica permisos"
        edutrack.api.risk -> edutrack.api.security "Verifica permisos"
        edutrack.api.reporting -> edutrack.api.security "Verifica permisos"
        edutrack.api.settings -> edutrack.api.security "Verifica permisos"

        edutrack.api.risk -> edutrack.api.settings "Lee umbrales"
        edutrack.api.risk -> edutrack.api.mlClient "Solicita predicciones"
        edutrack.api.risk -> edutrack.api.alerts "Entrega evaluaciones de riesgo alto o moderado"
        edutrack.api.mlClient -> edutrack.ml.router "POST /v1/predict/batch" "JSON/HTTP"
        edutrack.api.alerts -> email "Envía notificaciones" "SMTP"

        edutrack.api.security -> edutrack.api.repositories "Usuarios y tokens"
        edutrack.api.academic -> edutrack.api.repositories "Persiste"
        edutrack.api.imports -> edutrack.api.repositories "Persiste por lotes"
        edutrack.api.risk -> edutrack.api.repositories "Lee datos y guarda evaluaciones"
        edutrack.api.alerts -> edutrack.api.repositories "Guarda alertas y sugerencias"
        edutrack.api.reporting -> edutrack.api.repositories "Consulta agregados"
        edutrack.api.settings -> edutrack.api.repositories "Persiste"
        edutrack.api.repositories -> edutrack.db "Lee y escribe" "SQL/TCP"

        # Componentes del servicio ML
        edutrack.ml.router -> edutrack.ml.validator "Valida la entrada"
        edutrack.ml.router -> edutrack.ml.predictor "Solicita probabilidad"
        edutrack.ml.router -> edutrack.ml.explainer "Solicita factores"
        edutrack.ml.predictor -> edutrack.ml.loader "Obtiene el modelo"
        edutrack.ml.explainer -> edutrack.ml.loader "Obtiene el modelo"
        edutrack.ml.loader -> edutrack.modelStore "Lee el artefacto .joblib"

        # Despliegue
        deploymentEnvironment "Local" {
            deploymentNode "Laptop de desarrollo" "" "Windows 11, WSL2" {
                deploymentNode "Navegador web" "" "Chrome" {
                    containerInstance edutrack.spa
                }
                deploymentNode "Docker Compose" "" "Docker Engine" {
                    deploymentNode "proxy" "" "nginx:alpine" {
                        containerInstance edutrack.proxy
                    }
                    deploymentNode "api" "" "python:3.12-slim" {
                        containerInstance edutrack.api
                    }
                    deploymentNode "ml" "" "python:3.12-slim" {
                        containerInstance edutrack.ml
                    }
                    deploymentNode "mysql" "" "mysql:8.0" {
                        containerInstance edutrack.db
                    }
                    deploymentNode "models" "" "Volumen Docker" {
                        containerInstance edutrack.modelStore
                    }
                }
                deploymentNode "Entorno virtual" "" "Python 3.12 venv" {
                    containerInstance edutrack.training
                }
            }
        }

        deploymentEnvironment "Produccion" {
            deploymentNode "Dispositivo del usuario" "" "Navegador web" {
                containerInstance edutrack.spa
            }
            deploymentNode "Amazon Web Services" "" "AWS" {
                deploymentNode "us-east-1" "" "Región" {
                    deploymentNode "EC2" "" "Ubuntu 24.04, Docker Compose" {
                        deploymentNode "proxy" "" "nginx:alpine" {
                            containerInstance edutrack.proxy
                        }
                        deploymentNode "api" "" "python:3.12-slim" {
                            containerInstance edutrack.api
                        }
                        deploymentNode "ml" "" "python:3.12-slim" {
                            containerInstance edutrack.ml
                        }
                    }
                    deploymentNode "RDS" "" "MySQL 8.0" {
                        containerInstance edutrack.db
                    }
                    deploymentNode "S3" "" "Amazon S3" {
                        containerInstance edutrack.modelStore
                    }
                    deploymentNode "SES" "" "Amazon SES" {
                        softwareSystemInstance email
                    }
                }
            }
        }
    }

    views {
        systemContext edutrack "SystemContext" {
            include *
            autoLayout lr
            title "EduTrack - Contexto del sistema"
        }

        container edutrack "Containers" {
            include *
            autoLayout lr
            title "EduTrack - Contenedores"
        }

        component edutrack.api "ApiComponents" {
            include *
            autoLayout tb
            title "EduTrack - Componentes de la API principal"
        }

        component edutrack.ml "MlComponents" {
            include *
            autoLayout lr
            title "EduTrack - Componentes del servicio ML"
        }

        dynamic edutrack "PredictionFlow" {
            title "EduTrack - Flujo de evaluación de riesgo"
            analyst -> edutrack.spa "Selecciona periodo y aula, y ejecuta la evaluación"
            edutrack.spa -> edutrack.api "POST /api/v1/risk-assessments/run"
            edutrack.api -> edutrack.db "Lee notas, asistencia, conducta, encuestas y umbrales"
            edutrack.api -> edutrack.ml "Envía el lote de vectores de características"
            edutrack.api -> edutrack.db "Guarda evaluaciones, sugerencias y alertas"
            edutrack.api -> email "Notifica a tutores y padres"
            autoLayout lr
        }

        deployment edutrack "Local" "DeploymentLocal" {
            include *
            autoLayout lr
            title "EduTrack - Despliegue local"
        }

        deployment edutrack "Produccion" "DeploymentAWS" {
            include *
            autoLayout lr
            title "EduTrack - Despliegue en AWS"
        }

        styles {
            element "Element" {
                color #ffffff
            }
            element "Person" {
                shape Person
                background #08427b
            }
            element "Software System" {
                background #1168bd
            }
            element "External" {
                background #8c8c8c
            }
            element "Container" {
                background #438dd5
            }
            element "Component" {
                background #85bbf0
                color #000000
            }
            element "Web Browser" {
                shape WebBrowser
            }
            element "Database" {
                shape Cylinder
            }
            element "Storage" {
                shape Folder
            }
            element "Batch" {
                shape Hexagon
            }
            element "Proxy" {
                shape Pipe
            }
            element "Deployment Node" {
                background #ffffff
                color #000000
            }
            relationship "Relationship" {
                dashed false
            }
        }
    }
}
