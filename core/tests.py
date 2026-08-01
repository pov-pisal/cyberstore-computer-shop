from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Coupon, Review

class ComputerShopTests(TestCase):
    def setUp(self):
        # Set up a category and a product
        self.category = Category.objects.create(name="Test Category", slug="test-category")
        self.product = Product.objects.create(
            category=self.category,
            name="Test CPU",
            slug="test-cpu",
            sku="CPU-TST-01",
            description="A test central processing unit.",
            price=150.00,
            stock=10
        )
        self.client = Client()

    def test_product_creation(self):
        self.assertEqual(self.product.name, "Test CPU")
        self.assertEqual(self.product.get_image_url, "/static/images/placeholder.svg")

    def test_cart_totals(self):
        cart = Cart.objects.create()
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        
        self.assertEqual(cart.get_total_items, 2)
        self.assertEqual(cart.get_total_price, 300.00)

    def test_catalog_view(self):
        response = self.client.get(reverse('catalog'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test CPU")

    def test_catalog_json_view(self):
        response = self.client.get(reverse('catalog_json') + "?q=Test")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['products']), 1)
        self.assertEqual(data['products'][0]['name'], "Test CPU")

    def test_order_placement(self):
        cart = Cart.objects.create()
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        
        # We manually store cart in session to bypass view helper or test checkout POST
        # For simplicity, let's verify Order creation directly
        order = Order.objects.create(
            full_name="John Doe",
            email="john@example.com",
            phone="12345678",
            address="123 Test St",
            city="Phnom Penh",
            total_amount=150.00
        )
        OrderItem.objects.create(order=order, product=self.product, price=self.product.price, quantity=1)
        
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.total_amount, 150.00)

    def test_brand_filtering(self):
        self.product.brand = "Intel"
        self.product.save()
        
        response = self.client.get(reverse('catalog_json') + "?brand=Intel")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['products']), 1)
        self.assertEqual(data['products'][0]['brand'], "Intel")
        
        response_empty = self.client.get(reverse('catalog_json') + "?brand=AMD")
        self.assertEqual(response_empty.status_code, 200)
        data_empty = response_empty.json()
        self.assertEqual(len(data_empty['products']), 0)

    def test_add_product_authorization(self):
        response = self.client.post(reverse('add_product'), {
            'name': 'Test New CPU',
            'brand': 'AMD',
            'sku': 'NEW-AMD-CPU',
            'category': self.category.id,
            'price': '299.00',
            'stock': '10',
            'description': 'A new AMD processor.'
        })
        self.assertRedirects(response, reverse('home'))
        
        user = User.objects.create_user(username='normaluser', password='password123')
        self.client.login(username='normaluser', password='password123')
        response = self.client.post(reverse('add_product'), {
            'name': 'Test New CPU',
            'brand': 'AMD',
            'sku': 'NEW-AMD-CPU',
            'category': self.category.id,
            'price': '299.00',
            'stock': '10',
            'description': 'A new AMD processor.'
        })
        self.assertRedirects(response, reverse('home'))
        
        manager = User.objects.create_user(username='manageruser', password='password123')
        profile = manager.profile
        profile.is_manager = True
        profile.save()
        
        self.client.login(username='manageruser', password='password123')
        response = self.client.post(reverse('add_product'), {
            'name': 'Test New CPU',
            'brand': 'AMD',
            'sku': 'NEW-AMD-CPU',
            'category': self.category.id,
            'price': '299.00',
            'stock': '10',
            'description': 'A new AMD processor.',
            'specifications': '{"Cores": "8"}'
        })
        self.assertRedirects(response, '/dashboard/?tab=products')
        self.assertTrue(Product.objects.filter(sku='NEW-AMD-CPU').exists())

    def test_coupon_application(self):
        from .models import Coupon
        coupon = Coupon.objects.create(code="CYBER10", discount_percent=10, is_active=True)
        
        user = User.objects.create_user(username='testuser', password='password123')
        self.client.login(username='testuser', password='password123')
        user_cart, _ = Cart.objects.get_or_create(user=user)
        CartItem.objects.create(cart=user_cart, product=self.product, quantity=2) # 2 * 150 = 300
        
        response = self.client.post(
            reverse('apply_coupon'),
            data='{"code": "CYBER10"}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['code'], 'CYBER10')
        self.assertEqual(float(data['discount_amount']), 30.00)
        self.assertEqual(float(data['new_total']), 270.00)

    def test_product_reviews(self):
        from .models import Review
        user = User.objects.create_user(username='reviewer', password='password123')
        self.client.login(username='reviewer', password='password123')
        
        response = self.client.post(reverse('add_review'), {
            'product_id': self.product.id,
            'rating': 4,
            'comment': 'Good processor but runs a bit warm.'
        })
        self.assertRedirects(response, reverse('product_detail', kwargs={'slug': self.product.slug}))
        
        self.assertEqual(Review.objects.count(), 1)
        review = Review.objects.first()
        self.assertEqual(review.rating, 4)
        self.assertEqual(review.comment, 'Good processor but runs a bit warm.')
        self.assertEqual(self.product.average_rating, 4.0)
        self.assertEqual(self.product.review_count, 1)

    def test_pc_builder_view(self):
        response = self.client.get(reverse('pc_builder'))
        self.assertEqual(response.status_code, 200)

    def test_product_compare_view(self):
        response = self.client.get(reverse('product_compare') + f"?action=add&product_id={self.product.id}")
        self.assertEqual(response.status_code, 302)
        session = self.client.session
        self.assertIn(self.product.id, session.get('compare_ids', []))
        
        response_remove = self.client.get(reverse('product_compare') + f"?action=remove&product_id={self.product.id}")
        self.assertEqual(response_remove.status_code, 302)
        session = self.client.session
        self.assertNotIn(self.product.id, session.get('compare_ids', []))

    def test_track_order_view(self):
        order = Order.objects.create(
            full_name="Jane Doe",
            email="jane@example.com",
            phone="87654321",
            address="456 Track St",
            city="Siem Reap",
            total_amount=150.00
        )
        response = self.client.get(reverse('track_order') + f"?order_id={order.id}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jane Doe")
        
        response_fail = self.client.get(reverse('track_order') + "?order_id=9999")
        self.assertEqual(response_fail.status_code, 200)
        self.assertContains(response_fail, "Invalid Order ID or order not found")

    def test_manager_dashboard_extended(self):
        manager = User.objects.create_user(username='mng_extend', password='password123')
        profile = manager.profile
        profile.is_manager = True
        profile.save()
        self.client.login(username='mng_extend', password='password123')
        
        response = self.client.post(reverse('restock_product', kwargs={'product_id': self.product.id}), {'quantity': 15})
        self.assertRedirects(response, '/dashboard/?tab=overview')
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 25)
        
        response_add = self.client.post(reverse('add_coupon'), {
            'code': 'NEW25',
            'discount_percent': '25',
            'is_active': 'on'
        })
        self.assertRedirects(response_add, '/dashboard/?tab=coupons')
        self.assertTrue(Coupon.objects.filter(code='NEW25').exists())
        
        coupon = Coupon.objects.get(code='NEW25')
        response_del = self.client.get(reverse('delete_coupon', kwargs={'coupon_id': coupon.id}))
        self.assertRedirects(response_del, '/dashboard/?tab=coupons')
        self.assertFalse(Coupon.objects.filter(code='NEW25').exists())

    def test_manager_dashboard_additional_features(self):
        manager = User.objects.create_user(username='mng_additional', password='password123')
        profile = manager.profile
        profile.is_manager = True
        profile.save()
        self.client.login(username='mng_additional', password='password123')
        
        response_csv = self.client.get(reverse('export_orders_csv'))
        self.assertEqual(response_csv.status_code, 200)
        self.assertEqual(response_csv['Content-Type'], 'text/csv')
        self.assertIn('attachment; filename="cyberstore_orders.csv"', response_csv['Content-Disposition'])
        
        user = User.objects.create_user(username='reviewer_t', password='password123')
        review = Review.objects.create(
            product=self.product,
            user=user,
            rating=5,
            comment="Excellent computer item."
        )
        response_review_del = self.client.get(reverse('delete_review', kwargs={'review_id': review.id}))
        self.assertRedirects(response_review_del, '/dashboard/?tab=reviews')
        self.assertFalse(Review.objects.filter(id=review.id).exists())

    def test_manager_dashboard_roles(self):
        sale_user = User.objects.create_user(username='sales_rep', password='password123')
        sale_user.profile.role = 'sale'
        sale_user.profile.is_manager = True
        sale_user.profile.save()
        
        self.client.login(username='sales_rep', password='password123')
        response_sale = self.client.get('/dashboard/')
        self.assertEqual(response_sale.status_code, 200)
        self.assertContains(response_sale, "Manage Orders")
        self.assertContains(response_sale, "Manage Coupons")
        self.assertNotContains(response_sale, "Manage Products")
        self.assertNotContains(response_sale, "Manage Users")
        self.client.logout()

        it_user = User.objects.create_user(username='it_support', password='password123')
        it_user.profile.role = 'it'
        it_user.profile.is_manager = True
        it_user.profile.save()
        
        self.client.login(username='it_support', password='password123')
        response_it = self.client.get('/dashboard/')
        self.assertEqual(response_it.status_code, 200)
        self.assertContains(response_it, "Manage Products")
        self.assertContains(response_it, "Active Carts")
        self.assertNotContains(response_it, "Manage Orders")
        self.assertNotContains(response_it, "Manage Coupons")
        self.client.logout()

    def test_admin_change_user_password(self):
        admin_user = User.objects.create_user(username='admin_boss', password='password123')
        admin_user.profile.role = 'admin'
        admin_user.profile.is_manager = True
        admin_user.profile.save()
        
        target_user = User.objects.create_user(username='john_doe', password='oldpassword')
        
        self.client.login(username='admin_boss', password='password123')
        response = self.client.post(
            reverse('change_user_password', kwargs={'user_id': target_user.id}),
            {'new_password': 'newsecretpassword'}
        )
        self.assertRedirects(response, '/dashboard/?tab=users')
        
        self.client.logout()
        login_success = self.client.login(username='john_doe', password='newsecretpassword')
        self.assertTrue(login_success)

    def test_it_user_management_limits(self):
        it_user = User.objects.create_user(username='it_guy', password='password123')
        it_user.profile.role = 'it'
        it_user.profile.is_manager = True
        it_user.profile.save()
        
        admin_user = User.objects.create_user(username='admin_boss_2', password='password123')
        admin_user.profile.role = 'admin'
        admin_user.profile.is_manager = True
        admin_user.profile.save()
        
        self.client.login(username='it_guy', password='password123')
        
        response_list = self.client.get('/dashboard/?tab=users')
        self.assertEqual(response_list.status_code, 200)
        
        response_add_admin = self.client.post(reverse('add_user'), {
            'username': 'sneaky_admin',
            'email': 'sneaky@cyberstore.com',
            'password': 'password123',
            'role': 'admin'
        })
        self.assertRedirects(response_add_admin, '/dashboard/?tab=users')
        self.assertFalse(User.objects.filter(username='sneaky_admin').exists())
        
        response_add_sale = self.client.post(reverse('add_user'), {
            'username': 'sale_rep_2',
            'email': 'sale2@cyberstore.com',
            'password': 'password123',
            'role': 'sale'
        })
        self.assertRedirects(response_add_sale, '/dashboard/?tab=users')
        self.assertTrue(User.objects.filter(username='sale_rep_2').exists())
        sale_created = User.objects.get(username='sale_rep_2')
        self.assertEqual(sale_created.profile.role, 'sale')
        
        response_toggle = self.client.get(reverse('toggle_user_role', kwargs={'user_id': sale_created.id}) + "?role=admin")
        self.assertRedirects(response_toggle, '/dashboard/?tab=users')
        sale_created.refresh_from_db()
        self.assertEqual(sale_created.profile.role, 'sale')
        
        response_toggle_admin = self.client.get(reverse('toggle_user_role', kwargs={'user_id': admin_user.id}) + "?role=customer")
        self.assertRedirects(response_toggle_admin, '/dashboard/?tab=users')
        admin_user.refresh_from_db()
        self.assertEqual(admin_user.profile.role, 'admin')
        
        response_pw_admin = self.client.post(reverse('change_user_password', kwargs={'user_id': admin_user.id}), {'new_password': 'hackedpassword'})
        self.assertRedirects(response_pw_admin, '/dashboard/?tab=users')
        
        self.client.logout()
        admin_login = self.client.login(username='admin_boss_2', password='password123')
        self.assertTrue(admin_login)

    def test_order_history_view(self):
        response_guest = self.client.get(reverse('order_history'))
        self.assertEqual(response_guest.status_code, 302)
        
        user = User.objects.create_user(username='customer_bob', password='password123')
        user.profile.role = 'customer'
        user.profile.save()
        
        order = Order.objects.create(
            user=user,
            full_name='Bob Builder',
            email='bob@cyberstore.com',
            phone='012345678',
            address='Street 123',
            city='Phnom Penh',
            country='Cambodia',
            total_amount=Decimal('45.00')
        )
        
        self.client.login(username='customer_bob', password='password123')
        response_auth = self.client.get(reverse('order_history'))
        self.assertEqual(response_auth.status_code, 200)
        self.assertContains(response_auth, "Order #")
        self.assertContains(response_auth, "Bob Builder")
        self.assertContains(response_auth, "$45.00")

