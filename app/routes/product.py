from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.auth.deps import get_current_user
from app.models.product import Product
from app.schemas.product import ProductCreate

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/")
def get_products(db: Session = Depends(get_db)):
    """Public — frontend product listing page needs this without auth."""
    return db.query(Product).all()


@router.post("/")
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user),
):
    product = Product(**data.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product
