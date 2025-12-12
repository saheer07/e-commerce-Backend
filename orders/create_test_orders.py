# Create this file: orders/management/commands/create_test_orders.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from orders.models import Order, OrderItem
from products.models import Product
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates test orders for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of test orders to create',
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Get or create test user
        user, created = User.objects.get_or_create(
            username='test_customer',
            defaults={
                'email': 'customer@example.com',
                'first_name': 'Test',
                'last_name': 'Customer'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Created test user: {user.username}'))
        
        # Get existing products or create sample ones
        products = list(Product.objects.all()[:5])
        
        if not products:
            self.stdout.write(self.style.WARNING('No products found. Creating sample products...'))
            product_names = [
                'Wireless Headphones',
                'Smart Watch',
                'Laptop Bag',
                'Wireless Mouse',
                'USB Cable'
            ]
            for name in product_names:
                product = Product.objects.create(
                    name=name,
                    description=f'Sample {name} for testing',
                    price=Decimal('999.99'),
                    stock=100
                )
                products.append(product)
            self.stdout.write(self.style.SUCCESS(f'Created {len(products)} sample products'))
        
        # Status options
        statuses = ['Pending', 'Ordered', 'Processing', 'Shipped', 'Delivered', 'Cancelled']
        payment_methods = ['COD', 'RAZORPAY', 'Online']
        
        # Create test orders
        created_orders = 0
        for i in range(count):
            # Vary the order date
            days_ago = i % 30
            order_date = timezone.now() - timedelta(days=days_ago)
            
            # Create order
            order = Order.objects.create(
                user=user,
                customer_name=f'Customer {i+1}',
                customer_email=f'customer{i+1}@example.com',
                customer_phone=f'+91{9000000000 + i}',
                address=f'{i+1} Test Street, Test City, Test State - {100000 + i}',
                total=Decimal('0.00'),  # Will be calculated
                delivery_charge=Decimal('50.00') if i % 2 == 0 else Decimal('0.00'),
                payment_method=payment_methods[i % len(payment_methods)],
                status=statuses[i % len(statuses)],
                tracking_number=f'TRK{1000000 + i}' if i % 3 == 0 else None,
                payment_status='COMPLETED' if i % 2 == 0 else 'PENDING',
            )
            
            # Set the created date
            order.purchased_at = order_date
            
            # Add cancellation reason if cancelled
            if order.status == 'Cancelled':
                order.cancellation_reason = 'Customer requested cancellation for testing purposes'
                order.cancelled_at = order_date + timedelta(hours=2)
            
            # Add estimated delivery for shipped orders
            if order.status == 'Shipped':
                order.estimated_delivery = (timezone.now() + timedelta(days=3)).date()
            
            # Create order items (1-3 items per order)
            num_items = (i % 3) + 1
            order_total = Decimal('0.00')
            
            for j in range(num_items):
                product = products[j % len(products)]
                quantity = (j % 3) + 1
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price
                )
                
                order_total += product.price * quantity
            
            # Update order total
            order.total = order_total + order.delivery_charge
            order.save()
            
            created_orders += 1
            self.stdout.write(f'Created order #{order.id} with {num_items} items')
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_orders} test orders!'))
        self.stdout.write(self.style.SUCCESS(f'Test user: {user.username} (password: testpass123)'))