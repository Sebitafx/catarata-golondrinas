from sqlalchemy import Column, Integer, Float, String, Boolean, Date, Index
from .database import Base


class HistoricoVisita(Base):
    __tablename__ = "historico_visitas"

    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False)
    hora = Column(Integer, nullable=False)  # 0-23
    temperatura_c = Column(Float, nullable=False)
    condicion_clima = Column(String, nullable=False)  # despejado/nublado/lluvia_ligera/lluvia_fuerte
    es_fin_de_semana = Column(Boolean, nullable=False, default=False)
    visitantes = Column(Integer, nullable=False, default=0)

    __table_args__ = (Index("ix_fecha_hora", "fecha", "hora"),)
