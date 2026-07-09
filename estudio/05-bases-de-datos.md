# Bases de Datos: PostgreSQL, SQLAlchemy, SQLite

> **Fecha:** 2026-07-08

## Las Tres Bases Que Usamos

| Base | Cuándo | Por qué |
|------|--------|---------|
| **PostgreSQL** | Producción / Integración | Base de datos real, transaccional |
| **SQLite** | Tests unitarios | Rápida, no necesita instalación |
| **ambas** | El código habla con SQLAlchemy | ORM abstrae las diferencias |

## SQLAlchemy — El ORM

Un ORM (Object-Relational Mapper) te permite hablar con la base de datos
usando objetos de Python en vez de SQL.

### Sin ORM:
```sql
SELECT * FROM users WHERE email = 'x@y.com';
```
Con eso tenés que parsear el resultado, convertirlo a objetos, etc.

### Con ORM (nosotros):
```python
user = db.query(User).filter(User.email == "x@y.com").first()
print(user.name)
```

### Nuestros modelos (4 tablas)

```python
class BrokerConfig(Base):         # Brokers disponibles
    name: str
    api_key: str | None
    active: bool = False

class AlertConfig(Base):          # Alertas programadas
    ticker: str
    strategy: str    # scalping / swing
    condition: str   # crossover, rsi_oversold, etc.

class Prediction(Base):           # Predicciones almacenadas
    ticker: str
    signal: str      # BUY / SELL / NEUTRAL
    outcome: str | None  # PENDING / CORRECT / INCORRECT

class WhatsAppConfig(Base):       # Config de WhatsApp
    phone_number: str
    connected: bool = False
```

### Sincrónico vs Asincrónico

El proyecto usa **solo SQLAlchemy sincrónico**:

```python
engine = create_engine(settings.database_url_sync)
SessionLocal = sessionmaker(bind=engine)
```

La URL `postgresql+asyncpg://...` existe en `.env` pero **no se usa**.
Todo es sincrónico con `psycopg2`.

### init_db() — Creación automática

```python
def init_db():
    Base.metadata.create_all(bind=engine)  # Crea tablas si no existen
```

**No hay migraciones.** Si cambiás un modelo, hay que borrar la tabla
a mano: `DROP TABLE ... CASCADE` y reiniciar.

## ¿Por qué SQLite en tests?

```python
# tests/conftest.py
os.environ.setdefault("DATABASE_URL_SYNC", "sqlite:///./test.db")
```

- SQLite no necesita servidor (es un archivo)
- Los tests arrancan al instante
- En CI no necesitamos Postgres para tests unitarios

## Persistencia de Resultados (Background Analyzer)

Para que los resultados del análisis en background sobrevivan a reinicios del servidor, se agregó el modelo `BackgroundResult`:

```python
# app/models.py
class BackgroundResult(Base):
    __tablename__ = "background_results"
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    signal  = Column(String(10), nullable=False)
    confidence = Column(Float, default=0.0)
    price = Column(Float, nullable=True)
    strategy = Column(String(50), default="scalping")
    interval = Column(String(10), default="5m")
    periods = Column(Integer, default=100)
    error = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
```

**¿Por qué no Alembic?** Por ahora `init_db()` llama a `Base.metadata.create_all()` que crea tablas automáticamente. Si el proyecto escala, migrar a Alembic.

## 📚 Para investigar más

| Tema | Por qué | Dónde |
|------|---------|-------|
| **Alembic** | Migraciones automáticas (imprescindible) | https://alembic.sqlalchemy.org/ |
| **SQLAlchemy 2.0** | El nuevo estilo (select(), etc.) | https://docs.sqlalchemy.org/en/20/changelog/whatsnew_20.html |
| **asyncpg** | PostgreSQL asincrónico nativo | https://github.com/MagicStack/asyncpg |
| **Índices en SQL** | Optimizar queries lentas | `CREATE INDEX CONCURRENTLY` |
| **Connection Pooling** | PgBouncer, SQLAlchemy pool | https://docs.sqlalchemy.org/en/20/core/pooling.html |
| **PostgreSQL EXPLAIN** | Entender planes de ejecución | `EXPLAIN ANALYZE SELECT ...` |
