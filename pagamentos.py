import calendar
import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, func, select, update
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Papel, Production, Quinzena, User
from ..schemas import QuinzenaOut, ResumoOut
from ..security import so_chefe, usuario_atual

router = APIRouter(tags=["pagamentos"])
_val = Production.quantidade * Production.valor_unitario


def _resumo_query():
    soma = lambda expr, cond: func.coalesce(func.sum(case((cond, expr), else_=0)), 0)
    return (select(User.id, User.nome, User.setor,
                   soma(Production.quantidade, Production.pago.is_(False)).label("bp"),
                   soma(_val, Production.pago.is_(False)).label("pe"),
                   soma(_val, Production.pago.is_(True)).label("re"))
            .outerjoin(Production, Production.usuario_id == User.id)
            .where(User.papel == Papel.operador).group_by(User.id).order_by(User.nome))


def _out(r) -> ResumoOut:
    return ResumoOut(usuario_id=r.id, nome=r.nome, setor=r.setor, bloquinhos_pendentes=r.bp,
                     pendente=r.pe, recebido=r.re, total=r.pe + r.re)


@router.get("/resumo", response_model=list[ResumoOut])
def resumo_geral(db: Session = Depends(get_db), _: User = Depends(so_chefe)):
    """Painel do Chefe: uma linha por usuário."""
    return [_out(r) for r in db.execute(_resumo_query()).all()]


@router.get("/resumo/meu", response_model=ResumoOut)
def resumo_meu(db: Session = Depends(get_db), u: User = Depends(usuario_atual)):
    r = db.execute(_resumo_query().where(User.id == u.id)).first()
    if not r:
        raise HTTPException(404, "Apenas operadores possuem resumo")
    return _out(r)


@router.post("/usuarios/{uid}/pagar", response_model=ResumoOut)
def pagar_usuario(uid: int, db: Session = Depends(get_db), _: User = Depends(so_chefe)):
    """Marca todo o pendente de um usuário como recebido."""
    db.execute(update(Production).where(Production.usuario_id == uid, Production.pago.is_(False)).values(pago=True))
    db.commit()
    r = db.execute(_resumo_query().where(User.id == uid)).first()
    if not r:
        raise HTTPException(404, "Usuário não encontrado")
    return _out(r)


@router.post("/quinzenas/fechar", response_model=QuinzenaOut, status_code=201)
def fechar_quinzena(db: Session = Depends(get_db), _: User = Depends(so_chefe)):
    """Marca todo o pendente como recebido e registra o fechamento."""
    total = db.scalar(select(func.coalesce(func.sum(_val), 0)).where(Production.pago.is_(False)))
    if not total:
        raise HTTPException(409, "Não há valores pendentes")
    hoje = dt.date.today()
    faixa = "01-15" if hoje.day <= 15 else f"16-{calendar.monthrange(hoje.year, hoje.month)[1]}"
    q = Quinzena(rotulo=f"{faixa}/{hoje.month:02d}", total=total)
    db.add(q)
    db.flush()
    db.execute(update(Production).where(Production.pago.is_(False)).values(pago=True, quinzena_id=q.id))
    db.commit()
    return q


@router.get("/quinzenas", response_model=list[QuinzenaOut])
def listar_quinzenas(db: Session = Depends(get_db), _: User = Depends(so_chefe)):
    return db.scalars(select(Quinzena).order_by(Quinzena.fechada_em.desc())).all()
