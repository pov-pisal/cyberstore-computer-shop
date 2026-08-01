import json
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Q
from .models import Product, Category, UserProfile, Cart, CartItem, Order, OrderItem, Coupon, Review

# Helper: Get or create cart, with guest-to-user merging
def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        # Check if there is an anonymous session cart to merge
        session_key = request.session.session_key
        if session_key:
            session_cart = Cart.objects.filter(session_key=session_key).first()
            if session_cart:
                for item in session_cart.items.all():
                    # Check if item already in user cart
                    user_item = CartItem.objects.filter(cart=cart, product=item.product).first()
                    if user_item:
                        user_item.quantity += item.quantity
                        user_item.save()
                        item.delete()
                    else:
                        item.cart = cart
                        item.save()
                session_cart.delete()
    else:
        if not request.session.session_key:
            request.session.create()
        session_key = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart

# Helper to serialize cart items
def serialize_cart(cart):
    items_data = []
    for item in cart.items.all().select_related('product'):
        items_data.append({
            'id': item.id,
            'product_id': item.product.id,
            'name': item.product.name,
            'price': str(item.product.price),
            'quantity': item.quantity,
            'image_url': item.product.get_image_url,
            'slug': item.product.slug,
            'cost': str(item.get_cost)
        })
    return {
        'items': items_data,
        'total_items': cart.get_total_items,
        'total_price': str(cart.get_total_price)
    }

def home(request):
    # Retrieve top 4 featured products
    featured_products = Product.objects.filter(is_active=True).order_by('-created_at')[:4]
    # Retrieve 4 best sellers (popular premium products)
    best_sellers = Product.objects.filter(is_active=True).order_by('-price')[:4]
    return render(request, 'core/home.html', {
        'featured_products': featured_products,
        'best_sellers': best_sellers
    })

def catalog(request):
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.all()
    for cat in categories:
        cat.brands = Product.objects.filter(category=cat, is_active=True).exclude(brand='').values_list('brand', flat=True).distinct().order_by('brand')
        cat.product_count = Product.objects.filter(category=cat, is_active=True).count()
    brands = Product.objects.filter(is_active=True).exclude(brand='').values_list('brand', flat=True).distinct().order_by('brand')
    
    category_slug = request.GET.get('category')
    active_category = None
    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=active_category)
        
    active_brand = request.GET.get('brand')
    if active_brand:
        products = products.filter(brand=active_brand)
        
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(sku__icontains=query) |
            Q(brand__icontains=query)
        )
        
    best_sellers = products.order_by('-price')[:2]
        
    context = {
        'products': products,
        'categories': categories,
        'brands': brands,
        'active_category': active_category,
        'active_brand': active_brand,
        'best_sellers': best_sellers
    }
    return render(request, 'core/catalog.html', context)

# AJAX Catalog Search API
def catalog_json(request):
    products = Product.objects.filter(is_active=True)
    
    category_slug = request.GET.get('category')
    if category_slug:
        products = products.filter(category__slug=category_slug)
        
    active_brand = request.GET.get('brand')
    if active_brand:
        products = products.filter(brand=active_brand)
        
    query = request.GET.get('q')
    if query:
        products = products.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) |
            Q(sku__icontains=query) |
            Q(brand__icontains=query)
        )
        
    products_data = []
    for p in products:
        products_data.append({
            'id': p.id,
            'name': p.name,
            'slug': p.slug,
            'description': p.description,
            'price': str(p.price),
            'stock': p.stock,
            'image_url': p.get_image_url,
            'category_name': p.category.name,
            'brand': p.brand,
            'average_rating': p.average_rating,
            'review_count': p.review_count
        })
    return JsonResponse({'products': products_data})

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    has_reviewed = False
    if request.user.is_authenticated:
        has_reviewed = Review.objects.filter(product=product, user=request.user).exists()
    reviews = product.reviews.all()
    related_products = product.get_related_products
    return render(request, 'core/detail.html', {
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
        'has_reviewed': has_reviewed
    })

# AJAX Cart Views
def cart_data(request):
    cart = get_or_create_cart(request)
    return JsonResponse(serialize_cart(cart))

def cart_add(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            product_id = data.get('product_id')
            quantity = int(data.get('quantity', 1))
            
            product = get_object_or_404(Product, id=product_id)
            if product.stock < quantity:
                return JsonResponse({'success': False, 'error': f'Only {product.stock} items left in stock.'})
                
            cart = get_or_create_cart(request)
            item, created = CartItem.objects.get_or_create(cart=cart, product=product)
            if not created:
                if product.stock < item.quantity + quantity:
                    return JsonResponse({'success': False, 'error': f'Cannot add more. Max available stock is {product.stock}.'})
                item.quantity += quantity
            else:
                item.quantity = quantity
            item.save()
            
            return JsonResponse({'success': True, **serialize_cart(cart)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def cart_update(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            change = int(data.get('change', 0))
            
            cart = get_or_create_cart(request)
            item = get_object_or_404(CartItem, id=item_id, cart=cart)
            
            new_qty = item.quantity + change
            if new_qty <= 0:
                item.delete()
            else:
                if item.product.stock < new_qty:
                    return JsonResponse({'success': False, 'error': 'Requested quantity exceeds available stock.'})
                item.quantity = new_qty
                item.save()
                
            return JsonResponse({'success': True, **serialize_cart(cart)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def cart_remove(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            item_id = data.get('item_id')
            
            cart = get_or_create_cart(request)
            item = get_object_or_404(CartItem, id=item_id, cart=cart)
            item.delete()
            
            return JsonResponse({'success': True, **serialize_cart(cart)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

# Checkout View
def checkout(request):
    cart = get_or_create_cart(request)
    if cart.get_total_items == 0:
        messages.warning(request, "Your cart is empty. Please add items to checkout.")
        return redirect('catalog')
        
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        city = request.POST.get('city')
        country = request.POST.get('country')
        
        # Verify stock check
        for item in cart.items.all():
            if item.product.stock < item.quantity:
                messages.error(request, f"Sorry, {item.product.name} is now out of stock or does not have enough inventory.")
                return redirect('checkout')
                
        # Check for coupon in session
        coupon_code = request.session.get('coupon_code')
        coupon = None
        discount_amount = Decimal('0.00')
        subtotal = cart.get_total_price
        
        if coupon_code:
            coupon = Coupon.objects.filter(code=coupon_code, is_active=True).first()
            if coupon:
                discount_amount = round(subtotal * Decimal(coupon.discount_percent) / Decimal(100), 2)
                
        total_amount = subtotal - discount_amount
        
        # Create Order
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            full_name=full_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            country=country,
            total_amount=total_amount,
            coupon=coupon,
            discount_amount=discount_amount
        )
        
        # Create Order Items and decrease stock
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity
            )
            item.product.stock -= item.quantity
            item.product.save()
            
        # Clear Cart & Coupon Session
        cart.items.all().delete()
        request.session.pop('coupon_code', None)
        
        return redirect('checkout_success', order_id=order.id)
        
    # Clear any leftover coupon code when rendering page initially
    request.session.pop('coupon_code', None)
    return render(request, 'core/checkout.html', {'cart': cart})

def checkout_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'core/checkout_success.html', {'order': order})

# User Auth Views
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    next_page = request.GET.get('next', 'home')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Logged in successfully as {username}!")
            
            # Check next parameter
            next_url = request.POST.get('next', 'home')
            if not next_url or next_url == '':
                next_url = 'home'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'core/login.html', {'next': next_page})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        address = request.POST.get('address')
        city = request.POST.get('city')
        country = request.POST.get('country')
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'core/register.html')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'core/register.html')
            
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Profile fields (UserProfile created automatically by signals, we update it)
        user.profile.phone = phone
        user.profile.address = address
        user.profile.city = city
        user.profile.country = country
        user.save()
        
        login(request, user)
        messages.success(request, "Registration successful!")
        return redirect('home')
        
    return render(request, 'core/register.html')

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('home')

# Manager Dashboard Views
def is_manager(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.is_manager

def dashboard_view(request):
    if not is_manager(request.user):
        messages.error(request, "Access denied. Only shop managers can access this dashboard.")
        return redirect('home')
        
    orders = Order.objects.all().order_by('-created_at')
    products = Product.objects.all().order_by('-created_at')
    categories = Category.objects.all().order_by('name')
    users = User.objects.all().order_by('-date_joined')
    carts = Cart.objects.all().order_by('-id')
    coupons = Coupon.objects.all().order_by('-id')
    reviews = Review.objects.all().order_by('-created_at')
    
    # Advanced Statistics
    completed_orders = Order.objects.filter(status='Completed')
    completed_orders_count = completed_orders.count()
    total_revenue = completed_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0.00
    total_orders_count = orders.count()
    pending_orders_count = Order.objects.filter(status='Pending').count()
    
    # Average Order Value (AOV)
    average_order_value = total_revenue / completed_orders_count if completed_orders_count > 0 else 0.00
    
    # Total Customers count
    total_customers_count = User.objects.filter(is_superuser=False).count()
    
    # Total Discount Applied
    total_discounts_applied = Order.objects.aggregate(Sum('discount_amount'))['discount_amount__sum'] or 0.00
    
    # Best Selling Product
    best_seller = OrderItem.objects.filter(order__status='Completed').values('product__name', 'product__brand').annotate(total_qty=Sum('quantity')).order_by('-total_qty').first()
    best_selling_product = f"{best_seller['product__brand']} {best_seller['product__name']} ({best_seller['total_qty']} sold)" if best_seller else "No Sales Yet"
    
    # Category sales distribution metrics
    max_qty = max([OrderItem.objects.filter(order__status='Completed', product__category=cat).aggregate(Sum('quantity'))['quantity__sum'] or 0 for cat in categories] + [1])
    category_sales = []
    for cat in categories:
        qty_sold = OrderItem.objects.filter(order__status='Completed', product__category=cat).aggregate(Sum('quantity'))['quantity__sum'] or 0
        rev = OrderItem.objects.filter(order__status='Completed', product__category=cat).aggregate(total_rev=Sum('price'))['total_rev'] or 0.00
        percent = (qty_sold / max_qty) * 100
        category_sales.append({
            'name': cat.name,
            'qty_sold': qty_sold,
            'revenue': rev,
            'percentage': percent,
        })
    category_sales = sorted(category_sales, key=lambda x: x['qty_sold'], reverse=True)
    
    # Low stock items (stock <= 5)
    low_stock_items = Product.objects.filter(stock__lte=5, is_active=True).order_by('stock')
    low_stock_count = low_stock_items.count()
    
    active_tab = request.GET.get('tab', 'overview')
    
    context = {
        'orders': orders,
        'products': products,
        'categories': categories,
        'users': users,
        'carts': carts,
        'coupons': coupons,
        'reviews': reviews,
        'total_revenue': total_revenue,
        'total_orders_count': total_orders_count,
        'pending_orders_count': pending_orders_count,
        'average_order_value': average_order_value,
        'total_customers_count': total_customers_count,
        'total_discounts_applied': total_discounts_applied,
        'best_selling_product': best_selling_product,
        'category_sales': category_sales,
        'low_stock_items': low_stock_items,
        'low_stock_count': low_stock_count,
        'active_tab': active_tab
    }
    return render(request, 'core/dashboard.html', context)


def restock_product(request, product_id):
    if not is_manager(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        try:
            qty = int(request.POST.get('quantity', 0))
            if qty > 0:
                product.stock += qty
                product.save()
                messages.success(request, f"Successfully restocked {qty} units of '{product.name}'. New stock: {product.stock}.")
            else:
                messages.error(request, "Restock quantity must be greater than zero.")
        except ValueError:
            messages.error(request, "Invalid restock quantity.")
    return redirect('/dashboard/?tab=overview')


def add_coupon(request):
    if not is_manager(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        discount_percent = request.POST.get('discount_percent')
        is_active = request.POST.get('is_active') == 'on'
        
        if not code or not discount_percent:
            messages.error(request, "Coupon code and discount percentage are required.")
        else:
            try:
                discount_percent = int(discount_percent)
                if discount_percent < 0 or discount_percent > 100:
                    messages.error(request, "Discount percent must be between 0 and 100.")
                else:
                    Coupon.objects.create(code=code, discount_percent=discount_percent, is_active=is_active)
                    messages.success(request, f"Promo code '{code}' created successfully.")
            except ValueError:
                messages.error(request, "Invalid discount percentage value.")
    return redirect('/dashboard/?tab=coupons')


def delete_coupon(request, coupon_id):
    if not is_manager(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
    coupon = get_object_or_404(Coupon, id=coupon_id)
    code = coupon.code
    coupon.delete()
    messages.success(request, f"Promo code '{code}' deleted successfully.")
    return redirect('/dashboard/?tab=coupons')

def update_order_status(request, order_id):
    if not is_manager(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
        
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            if new_status == 'Completed':
                order.is_paid = True
            order.save()
            messages.success(request, f"Order #{order.id} status updated to {new_status}.")
            
    return redirect('/dashboard/?tab=orders')

# 1. Product Management CRUD
def add_product(request):
    if not is_manager(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
        
    if request.method == 'POST':
        category_id = request.POST.get('category')
        name = request.POST.get('name')
        brand = request.POST.get('brand')
        sku = request.POST.get('sku')
        description = request.POST.get('description')
        price = request.POST.get('price')
        stock = request.POST.get('stock')
        image_url = request.POST.get('image_url', '') or ''
        is_active = request.POST.get('is_active') == 'on'
        
        specs_str = request.POST.get('specifications', '{}')
        try:
            specs = json.loads(specs_str)
        except Exception:
            messages.error(request, "Invalid JSON formatting in specifications. Must be valid JSON (e.g. {\"Key\": \"Value\"}).")
            return redirect('/dashboard/?tab=products')
            
        from django.utils.text import slugify
        slug = slugify(name)
        base_slug = slug
        counter = 1
        while Product.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        category = get_object_or_404(Category, id=category_id)
        
        try:
            Product.objects.create(
                category=category,
                name=name,
                slug=slug,
                sku=sku,
                brand=brand,
                description=description,
                price=price,
                stock=stock,
                specifications=specs,
                image_url=image_url,
                is_active=is_active
            )
            messages.success(request, f"Product '{name}' added successfully.")
        except Exception as e:
            messages.error(request, f"Error adding product: {str(e)}")
            
    return redirect('/dashboard/?tab=products')

def edit_product(request, product_id):
    if not is_manager(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
        
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        product.category = get_object_or_404(Category, id=request.POST.get('category'))
        product.name = request.POST.get('name')
        product.brand = request.POST.get('brand')
        product.sku = request.POST.get('sku')
        product.description = request.POST.get('description')
        product.price = request.POST.get('price')
        product.stock = request.POST.get('stock')
        product.image_url = request.POST.get('image_url', '') or ''
        product.is_active = request.POST.get('is_active') == 'on'
        
        specs_str = request.POST.get('specifications', '{}')
        try:
            specs = json.loads(specs_str)
            product.specifications = specs
        except Exception:
            messages.error(request, "Invalid JSON formatting in specifications. Must be valid JSON.")
            return redirect('/dashboard/?tab=products')
            
        try:
            product.save()
            messages.success(request, f"Product '{product.name}' updated successfully.")
        except Exception as e:
            messages.error(request, f"Error updating product: {str(e)}")
            
    return redirect('/dashboard/?tab=products')

def delete_product(request, product_id):
    if not is_manager(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
        
    product = get_object_or_404(Product, id=product_id)
    name = product.name
    product.delete()
    messages.success(request, f"Product '{name}' deleted successfully.")
    return redirect('/dashboard/?tab=products')

# 2. Category Management CRUD
def add_category(request):
    if not is_manager(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
        
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        
        from django.utils.text import slugify
        slug = slugify(name)
        base_slug = slug
        counter = 1
        while Category.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        try:
            Category.objects.create(name=name, slug=slug, description=description)
            messages.success(request, f"Category '{name}' created successfully.")
        except Exception as e:
            messages.error(request, f"Error adding category: {str(e)}")
            
    return redirect('/dashboard/?tab=categories')

def edit_category(request, category_id):
    if not is_manager(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
        
    category = get_object_or_404(Category, id=category_id)
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.description = request.POST.get('description')
        try:
            category.save()
            messages.success(request, f"Category '{category.name}' updated successfully.")
        except Exception as e:
            messages.error(request, f"Error updating category: {str(e)}")
            
    return redirect('/dashboard/?tab=categories')

def delete_category(request, category_id):
    if not is_manager(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
        
    category = get_object_or_404(Category, id=category_id)
    name = category.name
    category.delete()
    messages.success(request, f"Category '{name}' deleted successfully.")
    return redirect('/dashboard/?tab=categories')

# 3. User Role Management
def toggle_user_role(request, user_id):
    user_role = request.user.profile.role
    is_admin_or_it = request.user.is_superuser or user_role in ['admin', 'it']
    if not is_admin_or_it:
        messages.error(request, "Access denied.")
        return redirect('home')
        
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        messages.error(request, "You cannot modify your own roles.")
        return redirect('/dashboard/?tab=users')
        
    # IT Support restrictions on managing admin users
    if user_role == 'it' and not request.user.is_superuser:
        if target_user.is_superuser or target_user.profile.role == 'admin':
            messages.error(request, "IT Support is not permitted to manage Admin users.")
            return redirect('/dashboard/?tab=users')
            
        new_role = request.GET.get('role')
        if new_role == 'admin':
            messages.error(request, "IT Support cannot assign the Admin role.")
            return redirect('/dashboard/?tab=users')
            
        if request.GET.get('type') == 'staff':
            messages.error(request, "IT Support cannot modify staff flags.")
            return redirect('/dashboard/?tab=users')
            
    new_role = request.GET.get('role')
    if new_role in ['customer', 'admin', 'sale', 'it']:
        profile = target_user.profile
        profile.role = new_role
        profile.is_manager = (new_role in ['admin', 'sale', 'it'])
        profile.save()
        messages.success(request, f"User '{target_user.username}' role updated to '{profile.get_role_display()}'.")
    elif request.GET.get('type') == 'staff':
        target_user.is_staff = not target_user.is_staff
        target_user.save()
        messages.success(request, f"User '{target_user.username}' staff status updated.")
        
    return redirect('/dashboard/?tab=users')

# 4. Cart Management CRUD
def delete_cart(request, cart_id):
    if not is_manager(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
        
    cart = get_object_or_404(Cart, id=cart_id)
    cart.delete()
    messages.success(request, "Cart deleted successfully.")
    return redirect('/dashboard/?tab=carts')

# 5. User Creation CRUD
def add_user(request):
    user_role = request.user.profile.role
    is_admin_or_it = request.user.is_superuser or user_role in ['admin', 'it']
    if not is_admin_or_it:
        messages.error(request, "Access denied.")
        return redirect('home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        is_staff = request.POST.get('is_staff') == 'on'
        role = request.POST.get('role', 'customer')
        
        # IT support cannot create Admin users
        if user_role == 'it' and not request.user.is_superuser and role == 'admin':
            messages.error(request, "IT Support is not permitted to create Admin users.")
            return redirect('/dashboard/?tab=users')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, f"Username '{username}' already exists.")
            return redirect('/dashboard/?tab=users')
            
        try:
            new_user = User.objects.create_user(username=username, email=email, password=password)
            new_user.is_staff = is_staff
            new_user.save()
            
            profile = new_user.profile
            profile.role = role
            profile.is_manager = (role in ['admin', 'sale', 'it'])
            profile.save()
            
            messages.success(request, f"User account '{username}' created successfully with role '{profile.get_role_display()}'.")
        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")
            
    return redirect('/dashboard/?tab=users')


from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

def apply_coupon(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code', '').strip().upper()
            cart = get_or_create_cart(request)
            
            if cart.get_total_items == 0:
                return JsonResponse({'success': False, 'error': 'Cart is empty.'})
                
            coupon = Coupon.objects.filter(code=code, is_active=True).first()
            if not coupon:
                return JsonResponse({'success': False, 'error': 'Invalid or inactive promo code.'})
                
            subtotal = cart.get_total_price
            discount = round(subtotal * Decimal(coupon.discount_percent) / Decimal(100), 2)
            new_total = subtotal - discount
            
            request.session['coupon_code'] = coupon.code
            
            return JsonResponse({
                'success': True,
                'code': coupon.code,
                'discount_percent': coupon.discount_percent,
                'discount_amount': str(discount),
                'new_total': str(new_total),
                'message': f'Promo code {coupon.code} applied successfully!'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@login_required
@require_POST
def add_review(request):
    product_id = request.POST.get('product_id')
    product = get_object_or_404(Product, id=product_id)
    rating = int(request.POST.get('rating', 5))
    comment = request.POST.get('comment', '').strip()
    
    if not comment:
        messages.error(request, "Review comment cannot be empty.")
        return redirect('product_detail', slug=product.slug)
        
    if rating < 1 or rating > 5:
        messages.error(request, "Rating must be between 1 and 5.")
        return redirect('product_detail', slug=product.slug)
        
    try:
        Review.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={'rating': rating, 'comment': comment}
        )
        messages.success(request, "Thank you! Your review has been submitted.")
    except Exception as e:
        messages.error(request, f"Failed to submit review: {str(e)}")
        
    return redirect('product_detail', slug=product.slug)


def pc_builder(request):
    # Get all active products for builder categories
    categories = Category.objects.filter(slug__in=['cpus', 'gpus', 'ram', 'storage'])
    products_by_cat = {}
    for cat in categories:
        products_by_cat[cat.slug] = Product.objects.filter(category=cat, is_active=True, stock__gt=0)
    
    return render(request, 'core/pc_builder.html', {
        'products_by_cat': products_by_cat,
    })


def product_compare(request):
    compare_ids = request.session.get('compare_ids', [])
    action = request.GET.get('action')
    product_id = request.GET.get('product_id')
    
    if product_id:
        try:
            product_id = int(product_id)
            if action == 'add':
                if product_id not in compare_ids:
                    compare_ids.append(product_id)
                    if len(compare_ids) > 4:
                        compare_ids.pop(0)
                    request.session['compare_ids'] = compare_ids
                    request.session.modified = True
            elif action == 'remove':
                if product_id in compare_ids:
                    compare_ids.remove(product_id)
                    request.session['compare_ids'] = compare_ids
                    request.session.modified = True
        except ValueError:
            pass
            
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'status': 'ok', 'count': len(compare_ids)})
        return redirect('product_compare')
        
    products = Product.objects.filter(id__in=compare_ids)
    all_spec_keys = set()
    for p in products:
        if isinstance(p.specifications, dict):
            all_spec_keys.update(p.specifications.keys())
            
    return render(request, 'core/compare.html', {
        'products': products,
        'all_spec_keys': sorted(list(all_spec_keys)),
    })


def track_order(request):
    order_id = request.GET.get('order_id')
    order = None
    error = None
    
    if order_id:
        try:
            order = Order.objects.get(id=int(order_id))
        except (Order.DoesNotExist, ValueError):
            error = "Invalid Order ID or order not found."
            
    return render(request, 'core/track.html', {
        'order': order,
        'error': error,
        'order_id': order_id,
    })


def export_orders_csv(request):
    import csv
    from django.http import HttpResponse
    
    if not is_manager(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
        
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="cyberstore_orders.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Recipient Name', 'Email', 'Phone', 'Address', 'City', 'Total Amount ($)', 'Discount ($)', 'Status', 'Paid Status', 'Created At'])
    
    orders = Order.objects.all().order_by('-created_at')
    for o in orders:
        writer.writerow([
            o.id,
            o.full_name,
            o.email,
            o.phone,
            o.address,
            o.city,
            o.total_amount,
            o.discount_amount,
            o.status,
            'Paid' if o.is_paid else 'Unpaid',
            o.created_at.strftime('%Y-%m-%d %H:%M')
        ])
        
    return response


def delete_review(request, review_id):
    if not is_manager(request.user):
        messages.error(request, "Access denied.")
        return redirect('home')
        
    review = get_object_or_404(Review, id=review_id)
    prod_name = review.product.name
    review.delete()
    messages.success(request, f"Review for product '{prod_name}' has been successfully deleted.")
    return redirect('/dashboard/?tab=reviews')


@login_required
def change_user_password(request, user_id):
    user_role = request.user.profile.role
    is_admin_or_it = request.user.is_superuser or user_role in ['admin', 'it']
    if not is_admin_or_it:
        messages.error(request, "Access denied. Only System Admins or IT Support can reset passwords.")
        return redirect('home')
        
    if request.method == 'POST':
        target_user = get_object_or_404(User, id=user_id)
        
        # IT Support restrictions on managing admin users
        if user_role == 'it' and not request.user.is_superuser:
            if target_user.is_superuser or target_user.profile.role == 'admin':
                messages.error(request, "IT Support is not permitted to change password for Admin users.")
                return redirect('/dashboard/?tab=users')
                
        new_password = request.POST.get('new_password', '').strip()
        if len(new_password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
        else:
            target_user.set_password(new_password)
            target_user.save()
            messages.success(request, f"Password for user '{target_user.username}' has been updated successfully.")
            
    return redirect('/dashboard/?tab=users')


