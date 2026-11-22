from fastapi import APIRouter, Depends, Request

from src.constants.domain import Role
from src.controllers.reports import download
from src.models.db import rows, transaction
from src.schemas.inputs import LoanInput, Login, PlanInput, ReversalInput
from src.services import auth, ledger, plans
from src.services.catalog import catalog

router = APIRouter()
analyst = auth.roles(Role.ANALYST)
reviewer = auth.roles(Role.REVIEWER)


@router.post('/login')
def login(payload: Login, request: Request):
    return auth.login(payload, request.client.host)


@router.get('/me')
def me(user=Depends(auth.current_user)):
    return user


@router.get('/catalog')
def read_catalog(user=Depends(auth.current_user)):
    with transaction() as cursor:
        return catalog(cursor)


@router.get('/receipts')
def read_receipts(user=Depends(auth.current_user)):
    with transaction() as cursor:
        return ledger.ledger(cursor)


@router.post('/receipts/loans', status_code=201)
def sign_loan(data: LoanInput, user=Depends(analyst)):
    with transaction() as cursor:
        return ledger.add_loan(cursor, data, user)


@router.post('/receipts/reversals', status_code=201)
def sign_reversal(data: ReversalInput, user=Depends(analyst)):
    with transaction() as cursor:
        return ledger.add_reversal(cursor, data, user)


@router.get('/plans')
def read_plans(user=Depends(auth.current_user)):
    with transaction() as cursor:
        return plans.list_plans(cursor, user)


@router.post('/plans', status_code=201)
def create_plan(data: PlanInput, user=Depends(analyst)):
    with transaction() as cursor:
        return plans.add_plan(cursor, data, user)


@router.get('/runs')
def read_runs(user=Depends(auth.current_user)):
    with transaction() as cursor:
        return plans.list_runs(cursor, user)


@router.post('/plans/{plan_id}/runs', status_code=202)
def run_plan(plan_id: int, user=Depends(analyst)):
    with transaction() as cursor:
        return plans.enqueue(cursor, plan_id, user)


@router.get('/runs/{run_id}')
def read_run(run_id: int, user=Depends(auth.current_user)):
    with transaction() as cursor:
        return plans.get_run(cursor, run_id, user)[0]


@router.post('/runs/{run_id}/publish')
def publish(run_id: int, user=Depends(reviewer)):
    with transaction() as cursor:
        return plans.publish(cursor, run_id, user)


@router.get('/runs/{run_id}/export')
def export(run_id: int, user=Depends(auth.current_user)):
    return download(run_id, user)


@router.get('/audit')
def read_audit(user=Depends(reviewer)):
    with transaction() as cursor:
        return rows(cursor, 'SELECT actor,action,target,created_at FROM audit_log ORDER BY id DESC LIMIT 100')
