from fastapi import FastAPI, HTTPException, Depends, Path, Query
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Table, Column, Integer, String, Float, MetaData
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import asyncio
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Initialize FastAPI app
app = FastAPI()
app.mount("/static",StaticFiles(directory="static"),name="static")

# Database setup
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

# Define your tables as SQLAlchemy models
class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    gender = Column(String)
    contact = Column(String)
    email = Column(String)

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    price = Column(Float)
    quantity = Column(Integer)
    brand = Column(String)
    supplier = Column(String)
    old_stock = Column(Integer)
    category = Column(String)

class Billing(Base):
    __tablename__ = 'billing'
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer)
    total_amount = Column(Float)

class BillingDetail(Base):
    __tablename__ = 'billing_details'
    id = Column(Integer, primary_key=True, index=True)
    billing_id = Column(Integer)
    product_id = Column(Integer)
    quantity = Column(Integer)
    price = Column(Float)

@app.get("/",response_class=HTMLResponse)
async def read_route():
    with open(".\static\index.html") as file:
        return file.read()




# Create tables
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("startup")
async def on_startup():
    await init_db()

# Pydantic models
class CustomerCreate(BaseModel):
    name: str
    gender: str
    contact: str
    email: str

class ProductCreate(BaseModel):
    name: str
    price: float
    quantity: int
    brand: str
    supplier: str
    old_stock: int
    category: str

class BillingCreate(BaseModel):
    customer_id: int
    product_ids: List[int]
    quantities: List[int]

class BillingUpdate(BaseModel):
    customer_id: int
    product_ids: List[int]
    quantities: List[int]

class BillingDetailResponse(BaseModel):
    product_id: int
    quantity: int
    price: float
    product_name: str
    product_price: float

class BillingResponse(BaseModel):
    id: int
    customer_id: int
    total_amount: float
    items: List[BillingDetailResponse]

# Dependency
async def get_db():
    async with SessionLocal() as session:
        yield session

# Routes
@app.post("/add_customer/", response_model=dict)
async def add_customer(customer: CustomerCreate, db: AsyncSession = Depends(get_db)):
    async with db.begin():
        db_customer = Customer(**customer.dict())
        db.add(db_customer)
        await db.commit()
    return {"message": "Customer added successfully"}

@app.post("/add_product/", response_model=dict)
async def add_product(product: ProductCreate, db: AsyncSession = Depends(get_db)):
    async with db.begin():
        db_product = Product(**product.dict())
        db.add(db_product)
        await db.commit()
    return {"message": "Product added successfully"}

@app.get("/get_customers/", response_model=List[CustomerCreate])
async def get_customers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Customer))
    customers = result.scalars().all()
    return customers

@app.get("/get_products/", response_model=List[ProductCreate])
async def get_products(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Product))
    products = result.scalars().all()
    return products

@app.post("/add_billing/", response_model=dict)
async def add_billing(billing: BillingCreate, db: AsyncSession = Depends(get_db)):
    if len(billing.product_ids) != len(billing.quantities):
        raise HTTPException(status_code=400, detail="The number of product IDs must match the number of quantities")

    total_amount = 0
    async with db.begin():
        # Check if customer exists
        result = await db.execute(select(Customer).where(Customer.id == billing.customer_id))
        customer = result.scalar()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Calculate total amount
        for product_id, quantity in zip(billing.product_ids, billing.quantities):
            result = await db.execute(select(Product).where(Product.id == product_id))
            product = result.scalar()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")
            total_amount += product.price * quantity

        # Insert billing entry
        db_billing = Billing(customer_id=billing.customer_id, total_amount=total_amount)
        db.add(db_billing)
        await db.commit()
        billing_id = db_billing.id

        # Insert billing details
        for product_id, quantity in zip(billing.product_ids, billing.quantities):
            result = await db.execute(select(Product).where(Product.id == product_id))
            product = result.scalar()
            db_detail = BillingDetail(billing_id=billing_id, product_id=product_id, quantity=quantity, price=product.price)
            db.add(db_detail)
        await db.commit()

    return {"message": "Billing entry created successfully", "total_amount": total_amount}

@app.get("/get_bill/{bill_id}", response_model=BillingResponse)
async def get_bill(bill_id: int, db: AsyncSession = Depends(get_db)):
    async with db.begin():
        # Fetch the billing entry
        result = await db.execute(select(Billing).where(Billing.id == bill_id))
        billing_entry = result.scalar()
        if billing_entry is None:
            raise HTTPException(status_code=404, detail="Bill not found")

        # Fetch billing details
        result = await db.execute(select(BillingDetail).where(BillingDetail.billing_id == bill_id))
        details = result.scalars().all()

        items = []
        for detail in details:
            result = await db.execute(select(Product).where(Product.id == detail.product_id))
            product = result.scalar()
            if product:
                items.append(BillingDetailResponse(
                    product_id=detail.product_id,
                    quantity=detail.quantity,
                    price=detail.price * detail.quantity,
                    product_name=product.name,
                    product_price=product.price
                ))

    return BillingResponse(
        id=billing_entry.id,
        customer_id=billing_entry.customer_id,
        total_amount=billing_entry.total_amount,
        items=items
    )

@app.put("/update_bill/{bill_id}", response_model=dict)
async def update_bill(bill_id: int, billing: BillingUpdate, db: AsyncSession = Depends(get_db)):
    if len(billing.product_ids) != len(billing.quantities):
        raise HTTPException(status_code=400, detail="The number of product IDs must match the number of quantities")

    total_amount = 0
    async with db.begin():
        # Check if the bill exists
        result = await db.execute(select(Billing).where(Billing.id == bill_id))
        existing_bill = result.scalar()
        if not existing_bill:
            raise HTTPException(status_code=404, detail="Bill not found")

        # Update billing total amount
        for product_id, quantity in zip(billing.product_ids, billing.quantities):
            result = await db.execute(select(Product).where(Product.id == product_id))
            product = result.scalar()
            if not product:
                raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")
            total_amount += product.price * quantity

        await db.execute(
            Billing.__table__.update().where(Billing.id == bill_id).values(customer_id=billing.customer_id, total_amount=total_amount)
        )

        # Delete existing billing details and insert new ones
        await db.execute(BillingDetail.__table__.delete().where(BillingDetail.billing_id == bill_id))
        for product_id, quantity in zip(billing.product_ids, billing.quantities):
            result = await db.execute(select(Product).where(Product.id == product_id))
            product = result.scalar()
            if product:
                db_detail = BillingDetail(billing_id=bill_id, product_id=product_id, quantity=quantity, price=product.price)
                db.add(db_detail)
        await db.commit()

    return {"message": "Bill updated successfully", "total_amount": total_amount}

@app.delete("/delete_bill/{bill_id}", response_model=dict)
async def delete_bill(bill_id: int, db: AsyncSession = Depends(get_db)):
    async with db.begin():
        # Check if the bill exists
        result = await db.execute(select(Billing).where(Billing.id == bill_id))
        existing_bill = result.scalar()
        if not existing_bill:
            raise HTTPException(status_code=404, detail="Bill not found")

        # Delete billing and billing details
        await db.execute(Billing.__table__.delete().where(Billing.id == bill_id))
        await db.execute(BillingDetail.__table__.delete().where(BillingDetail.billing_id == bill_id))

    return {"message": "Bill deleted successfully"}

# Utility function to get product price
async def get_product_price(db: AsyncSession, product_id: int) -> float:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar()
    if product:
        return product.price
    else:
        raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
