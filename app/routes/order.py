from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth.deps import get_current_user
from app.models.order import Order
from app.models.product import Product
from app.schemas.order import OrderCreate

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.get("/")
def get_my_orders(
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    """Return only the orders belonging to the logged-in user."""
    return db.query(Order).filter(Order.user_id == user_id).all()


@router.post("/")
def create_order(
    data: OrderCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.stock < data.quantity:
        raise HTTPException(status_code=400, detail="Not enough stock available")

    total_price = float(product.price) * data.quantity

    product.stock -= data.quantity  # reduce available stock

    order = Order(
        user_id=user_id,          # taken from JWT, not from request body
        product_id=data.product_id,
        quantity=data.quantity,
        total_price=total_price,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
