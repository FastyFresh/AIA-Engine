"""
Seed Stripe Products - Create subscription tiers for AI Influencer bots
Run this script once to set up the products in Stripe.

Usage: python scripts/seed_stripe_products.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.stripe_client import get_stripe_client_sync

PRODUCTS = [
    {
        "name": "Companion Tier",
        "description": "500 messages/month, exclusive photos, conversation memory",
        "metadata": {
            "tier_id": "companion",
            "monthly_messages": "500"
        },
        "price_cents": 999,
        "currency": "usd",
        "interval": "month"
    },
    {
        "name": "VIP Tier", 
        "description": "Unlimited messages, custom photo requests, video content, premium experience",
        "metadata": {
            "tier_id": "vip",
            "monthly_messages": "-1"
        },
        "price_cents": 2499,
        "currency": "usd",
        "interval": "month"
    }
]


def create_products():
    """Create all subscription products and prices"""
    stripe = get_stripe_client_sync()
    
    created_products = []
    
    for product_def in PRODUCTS:
        tier_id = product_def["metadata"]["tier_id"]
        
        existing = stripe.Product.search(query=f"name:'{product_def['name']}'")
        
        if existing.data:
            print(f"Product '{product_def['name']}' already exists: {existing.data[0].id}")
            product = existing.data[0]
        else:
            product = stripe.Product.create(
                name=product_def["name"],
                description=product_def["description"],
                metadata=product_def["metadata"]
            )
            print(f"Created product: {product.id} - {product.name}")
        
        prices = stripe.Price.list(product=product.id, active=True)
        matching_price = None
        for p in prices.data:
            if (p.unit_amount == product_def["price_cents"] and 
                p.currency == product_def["currency"] and
                p.recurring and p.recurring.interval == product_def["interval"]):
                matching_price = p
                break
        
        if matching_price:
            print(f"  Price already exists: {matching_price.id} (${matching_price.unit_amount/100:.2f}/{matching_price.recurring.interval})")
            price = matching_price
        else:
            price = stripe.Price.create(
                product=product.id,
                unit_amount=product_def["price_cents"],
                currency=product_def["currency"],
                recurring={"interval": product_def["interval"]}
            )
            print(f"  Created price: {price.id} (${price.unit_amount/100:.2f}/{price.recurring.interval})")
        
        created_products.append({
            "tier_id": tier_id,
            "product_id": product.id,
            "price_id": price.id,
            "price_cents": price.unit_amount
        })
    
    print("\n--- Summary ---")
    print("Add these price IDs to your bot config:")
    for p in created_products:
        print(f"  {p['tier_id']}: {p['price_id']}")
    
    return created_products


if __name__ == "__main__":
    print("Creating Stripe subscription products...\n")
    try:
        products = create_products()
        print("\nDone! Products created successfully.")
    except Exception as e:
        print(f"\nError: {e}")
        raise
