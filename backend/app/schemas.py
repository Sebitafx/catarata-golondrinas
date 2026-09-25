from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field


CONDICIONES = ["despejado", "nublado", "lluvia_ligera", "lluvia_fuerte"]


class HistoricoCreate(BaseModel):
    fecha: date
    hora: int = Field(ge=0, le=23)
    temperatura_c: float = Field(ge=-10, le=50)
    condicion_clima: str = Field(pattern="^(despejado|nublado|lluvia_ligera|lluvia_fuerte)$")
    es_fin_de_semana: bool = False
    visitantes: int = Field(ge=0, le=200)


class HistoricoOut(HistoricoCreate):
    id: int

    class Config:
        from_attributes = True


class HistoricoPaginado(BaseModel):
    total: int
    page: int
    size: int
    items: List[HistoricoOut]


class ClimaActual(BaseModel):
    temperatura_c: float
    condicion: str
    descripcion: str
    humedad: int
    hora_consulta: str
    fuente: str = "openweathermap"
    lat: float
    lon: float


class ClimaUsado(BaseModel):
    temperatura_c: float
    condicion: str


class PrediccionOut(BaseModel):
    hora: int
    fecha: str
    es_fin_de_semana: bool
    clima_usado: ClimaUsado
    visitantes_estimados: int
    aforo_max: int = 40
    nota: Optional[str] = None


class PronosticoBloque(BaseModel):
    hora_consulta: str
    temperatura_c: float
    condicion: str
    descripcion: str
    humedad: int


class PronosticoOut(BaseModel):
    fuente: str = "openweathermap"
    bloques: List[PronosticoBloque]
