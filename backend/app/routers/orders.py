from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.order import Order, OrderStatus
from app.schemas.order import OrderCreate, OrderUpdate, OrderResponse
from app.auth.dependencies import get_current_user

router = APIRouter()


@router.get("", summary="発注一覧")
def list_orders(
    page: int = 1,
    per_page: int = 20,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/{order_id}", response_model=OrderResponse, summary="発注詳細")
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="発注が見つかりません")
    return order


@router.post("", response_model=OrderResponse, status_code=201, summary="発注作成")
def create_order(
    req: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = Order(**req.model_dump())
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


@router.put("/{order_id}", response_model=OrderResponse, summary="発注更新")
def update_order(
    order_id: int,
    req: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="発注が見つかりません")
    update_data = req.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(order, key, value)
    db.commit()
    db.refresh(order)
    return order


@router.delete("/{order_id}", status_code=204, summary="発注削除")
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="発注が見つかりません")
    db.delete(order)
    db.commit()


@router.post("/{order_id}/confirm", response_model=OrderResponse, summary="発注確認")
def confirm_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="発注が見つかりません")
    if order.status != OrderStatus.pending:
        raise HTTPException(status_code=400, detail="保留中の発注のみ確認できます")
    order.status = OrderStatus.confirmed
    order.confirmed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(order)
    return order
