"""Seed deterministic Phase 5 demo commerce data (10 customers, 240 orders)."""
import uuid
from datetime import UTC,datetime
from decimal import Decimal
import psycopg

URL="postgresql://nexusai:nexusai_dev_password@localhost:5432/nexusai"
NS=uuid.UUID("cad51b5b-3f10-45c1-a3e5-f66bcad57a63")

def main():
    with psycopg.connect(URL) as connection:
        with connection.transaction():
            for rid,name in enumerate(("North","South","East","West"),1):connection.execute("INSERT INTO demo_regions(id,name) VALUES(%s,%s) ON CONFLICT(id) DO UPDATE SET name=excluded.name",(rid,name))
            for pid,(name,category) in enumerate((("Atlas Laptop","Computing"),("Beacon Phone","Mobile"),("Cloud Monitor","Display"),("Delta Dock","Accessory"),("Echo Tablet","Mobile")),1):connection.execute("INSERT INTO demo_products(id,name,category) VALUES(%s,%s,%s) ON CONFLICT(id) DO UPDATE SET name=excluded.name,category=excluded.category",(pid,name,category))
            customers=[]
            for index in range(1,11):
                cid=uuid.uuid5(NS,f"customer-{index}");code=f"C{1000+index}";customers.append((cid,code))
                connection.execute("INSERT INTO customer_profiles(id,customer_code,name,email,region_id,tier,created_at,updated_at) VALUES(%s,%s,%s,%s,%s,%s,now(),now()) ON CONFLICT(customer_code) DO UPDATE SET name=excluded.name,email=excluded.email,region_id=excluded.region_id,tier=excluded.tier,updated_at=now()",(cid,code,f"Demo Customer {index}",f"customer{index}@demo.local",(index-1)%4+1,"enterprise" if index<=2 else "standard"))
            for index in range(240):
                customer_id,code=customers[index%10];region=index%4+1;product=index%5+1;month=index%24+1;year=2025 if month<=12 else 2026;month=((month-1)%12)+1
                order_id=uuid.uuid5(NS,f"order-{index}");order_code=f"O{20250000+index+1}";growth={1:1.45,2:1.25,3:1.1,4:.95}[region] if year==2026 else 1
                amount=Decimal(str(round((180+(index%17)*37)*growth,2)));ordered=datetime(year,month,(index%25)+1,12,tzinfo=UTC)
                connection.execute("INSERT INTO customer_orders(id,order_code,customer_id,product_id,region_id,quantity,amount,status,refund_status,ordered_at) VALUES(%s,%s,%s,%s,%s,%s,%s,'delivered','none',%s) ON CONFLICT(order_code) DO UPDATE SET amount=excluded.amount,status=excluded.status,ordered_at=excluded.ordered_at",(order_id,order_code,customer_id,product,region,index%4+1,amount,ordered))
            connection.execute("INSERT INTO customer_orders(id,order_code,customer_id,product_id,region_id,quantity,amount,status,refund_status,ordered_at) VALUES(%s,'O10001',%s,1,1,1,1200,'delivered','none',now()-interval '10 days') ON CONFLICT(order_code) DO UPDATE SET ordered_at=excluded.ordered_at,status='delivered',refund_status='none'",(uuid.uuid5(NS,"order-special"),customers[0][0]))
    print("Seeded 4 regions, 5 products, 10 customers, 240 deterministic orders")

if __name__=="__main__":main()
