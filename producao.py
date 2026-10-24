import calendar
import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Papel, Production, User
from ..schemas import DiaOut, ProducaoIn, ProducaoOut
from ..security import so_chefe, usuario_atual
from .config import _cfg

router = APIRouter(prefix="/producao", tags=["produção"])


def _alvo(u: User, usuario_id: int | None) -> int:
    """Operador só enxerga os próprios dados; Chefe precisa dizer de quem."""
    if u.papel == Papel.operador:
        return u.id
    if usuario_id is None:
        raise HTTPException(422, "Informe usuario_id")
    return usuario_id


@router.post("", response_model=ProducaoOut, status_code=201)
def lancar(d: ProducaoIn, db: Session = Depends(get_db), _: User = Depends(so_chefe)):
    alvo = db.get(User, d.usuario_id)
    if not alvo or alvo.papel != Papel.operador:
        raise HTTPException(404, "Usuário não encontrado")
    valor = _cfg(db).valor_bloquinho
    if valor <= 0:
        raise HTTPException(409, "Defina o valor por bloquinho antes de lançar")
    p = Production(usuario_id=alvo.id, data=d.data, quantidade=d.quantidade, valor_unitario=valor)
    db.add(p)
    db.commit()
    return p


@router.get("", response_model=list[ProducaoOut])
def listar(usuario_id: int | None = None, inicio: dt.date | None = None, fim: dt.date | None = None,
           pago: bool | None = None, db: Session = Depends(get_db), u: User = Depends(usuario_atual)):
    q = select(Production).where(Production.usuario_id == _alvo(u, usuario_id))
    if inicio:
        q = q.where(Production.data >= inicio)
    if fim:
        q = q.where(Production.data <= fim)
    if pago is not None:
        q = q.where(Production.pago.is_(pago))
    return db.scalars(q.order_by(Production.data.desc(), Production.id.desc())).all()


@router.get("/calendario", response_model=list[DiaOut])
def calendario(ano: int = Query(ge=2000, le=2100), mes: int = Query(ge=1, le=12),
               usuario_id: int | None = None, db: Session = Depends(get_db), u: User = Depends(usuario_atual)):
    ini, fim = dt.date(ano, mes, 1), dt.date(ano, mes, calendar.monthrange(ano, mes)[1])
    rows = db.execute(
        select(Production.data, func.sum(Production.quantidade),
               func.sum(Production.quantidade * Production.valor_unitario))
        .where(Production.usuario_id == _alvo(u, usuario_id), Production.data.between(ini, fim))
        .group_by(Production.data).order_by(Production.data)).all()
    return [DiaOut(data=d, quantidade=q, total=t) for d, q, t in rows]


@router.delete("/{pid}", status_code=204)
def excluir(pid: int, db: Session = Depends(get_db), _: User = Depends(so_chefe)):
    p = db.get(Production, pid)
    if not p:
        raise HTTPException(404, "Lançamento não encontrado")
    if p.pago:
        raise HTTPException(409, "Lançamento já pago não pode ser excluído")
    db.delete(p)
    db.commit()
