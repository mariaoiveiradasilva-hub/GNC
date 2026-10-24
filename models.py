import datetime as dt
import enum
from decimal import Decimal

from sqlalchemy import (Boolean, Date, DateTime, Enum, ForeignKey, Index,
                        Integer, Numeric, String, UniqueConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Papel(str, enum.Enum):
    chefe = "chefe"
    operador = "operador"


class Setor(str, enum.Enum):
    selado = "Selado"
    embalado = "Embalado"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("nome", "telefone"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    telefone: Mapped[str | None] = mapped_column(String(20))  # só dígitos
    email: Mapped[str | None] = mapped_column(String(160), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(100))
    papel: Mapped[Papel] = mapped_column(Enum(Papel, name="papel"))
    setor: Mapped[Setor | None] = mapped_column(Enum(Setor, name="setor"))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Setting(Base):
    """Linha única (id=1) com o valor por bloquinho, igual para todos."""
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    valor_bloquinho: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)


class Quinzena(Base):
    __tablename__ = "quinzenas"

    id: Mapped[int] = mapped_column(primary_key=True)
    rotulo: Mapped[str] = mapped_column(String(20))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    fechada_em: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Production(Base):
    __tablename__ = "production_logs"
    __table_args__ = (Index("ix_prod_user_data", "usuario_id", "data"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    data: Mapped[dt.date] = mapped_column(Date)
    quantidade: Mapped[int] = mapped_column(Integer)
    valor_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))  # valor vigente no lançamento
    pago: Mapped[bool] = mapped_column(Boolean, default=False)
    quinzena_id: Mapped[int | None] = mapped_column(ForeignKey("quinzenas.id", ondelete="SET NULL"))
    criado_em: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @property
    def total(self) -> Decimal:
        return self.quantidade * self.valor_unitario
