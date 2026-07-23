// Computer Shop Main JS Logic - Cart and Filter interactions

document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const cartBtn = document.getElementById('cart-toggle-btn');
    const closeCartBtn = document.getElementById('close-cart-btn');
    const cartSidebar = document.getElementById('cart-sidebar');
    const cartOverlay = document.getElementById('cart-overlay');
    
    // Toggle Cart Drawer
    if (cartBtn && cartSidebar && cartOverlay) {
        const toggleCart = () => {
            cartSidebar.classList.toggle('open');
            cartOverlay.classList.toggle('open');
            if (cartSidebar.classList.contains('open')) {
                fetchCartData();
            }
        };
        
        cartBtn.addEventListener('click', toggleCart);
        closeCartBtn.addEventListener('click', toggleCart);
        cartOverlay.addEventListener('click', toggleCart);
    }
    
    // CSRF Token Helper
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // Global cart function to expose
    window.addToCart = function(productId, qty = 1) {
        fetch('/cart/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ product_id: productId, quantity: qty })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                updateCartBadges(data.total_items);
                // Open cart sidebar to show user it was added
                if (cartSidebar && !cartSidebar.classList.contains('open')) {
                    cartSidebar.classList.add('open');
                    cartOverlay.classList.add('open');
                }
                renderCartItems(data.items, data.total_price);
            } else {
                alert(data.error || 'Failed to add item to cart');
            }
        })
        .catch(err => console.error('Error adding to cart:', err));
    };

    window.updateCartQty = function(itemId, change) {
        fetch('/cart/update/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ item_id: itemId, change: change })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                updateCartBadges(data.total_items);
                renderCartItems(data.items, data.total_price);
                // If on checkout page, reload to sync
                if (window.location.pathname.includes('/checkout/')) {
                    window.location.reload();
                }
            } else {
                alert(data.error || 'Failed to update quantity');
            }
        })
        .catch(err => console.error('Error updating cart:', err));
    };

    window.removeFromCart = function(itemId) {
        fetch('/cart/remove/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({ item_id: itemId })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                updateCartBadges(data.total_items);
                renderCartItems(data.items, data.total_price);
                // If on checkout page, reload to sync
                if (window.location.pathname.includes('/checkout/')) {
                    window.location.reload();
                }
            }
        })
        .catch(err => console.error('Error removing item:', err));
    };

    function fetchCartData() {
        fetch('/cart/data/')
        .then(res => res.json())
        .then(data => {
            updateCartBadges(data.total_items);
            renderCartItems(data.items, data.total_price);
        });
    }

    function updateCartBadges(count) {
        const badges = document.querySelectorAll('.cart-badge');
        badges.forEach(badge => {
            badge.innerText = count;
            badge.style.display = count > 0 ? 'flex' : 'none';
        });
    }

    function renderCartItems(items, totalPrice) {
        const listContainer = document.getElementById('cart-items-list');
        const subtotalElement = document.getElementById('cart-subtotal');
        
        if (!listContainer) return;
        
        if (items.length === 0) {
            listContainer.innerHTML = `
                <div style="text-align: center; color: var(--text-muted); margin-top: 40px;">
                    <svg width="48" height="48" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="margin-bottom: 12px; opacity: 0.5;">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z"></path>
                    </svg>
                    <p>Your shopping cart is empty</p>
                </div>
            `;
            if (subtotalElement) subtotalElement.innerText = '$0.00';
            return;
        }
        
        let html = '';
        items.forEach(item => {
            html += `
                <div class="cart-item-row">
                    <img src="${item.image_url}" alt="${item.name}" class="cart-item-img">
                    <div class="cart-item-details">
                        <h4>${item.name}</h4>
                        <div class="cart-item-price">$${parseFloat(item.price).toFixed(2)}</div>
                        <div class="cart-qty-controls">
                            <button class="cart-qty-btn" onclick="updateCartQty(${item.id}, -1)">-</button>
                            <span class="cart-qty-val">${item.quantity}</span>
                            <button class="cart-qty-btn" onclick="updateCartQty(${item.id}, 1)">+</button>
                        </div>
                    </div>
                    <div class="cart-item-remove">
                        <button class="cart-item-remove-btn" onclick="removeFromCart(${item.id})">
                            <svg width="18" height="18" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                            </svg>
                        </button>
                    </div>
                </div>
            `;
        });
        
        listContainer.innerHTML = html;
        if (subtotalElement) {
            subtotalElement.innerText = '$' + parseFloat(totalPrice).toFixed(2);
        }
        const headerCartPrices = document.querySelectorAll('.header-cart-price');
        headerCartPrices.forEach(el => {
            el.innerText = '$' + parseFloat(totalPrice).toFixed(2);
        });
    }

    // Dynamic filtering for catalog search & category selections without full page reload
    // Dynamic filtering for catalog search & category/brand selections without full page reload
    const searchInput = document.getElementById('search-catalog');
    if (searchInput) {
        let delayTimer;
        searchInput.addEventListener('input', () => {
            clearTimeout(delayTimer);
            delayTimer = setTimeout(() => {
                filterCatalog();
                updateURLHistory();
            }, 300); // Debounce search
        });
    }

    // Handle AJAX filtering click events on categories
    const categoryItems = document.querySelectorAll('.category-item');
    categoryItems.forEach(item => {
        const link = item.querySelector('a');
        if (link) {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                categoryItems.forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                
                // Reset brand filter to all when clicking a general category
                const customOptions = document.querySelectorAll('#brand-options-list .custom-option');
                const selectLabel = document.getElementById('brand-select-label');
                customOptions.forEach(opt => {
                    opt.classList.remove('selected');
                    if (opt.dataset.value === 'all') {
                        opt.classList.add('selected');
                        if (selectLabel) selectLabel.innerText = 'All Brands';
                    }
                });

                // Reset all selected flyout brand items
                const flyoutBrandItems = document.querySelectorAll('.flyout-brand-item');
                flyoutBrandItems.forEach(i => i.classList.remove('selected'));

                filterCatalog();
                updateURLHistory();
            });
        }
    });

    // Handle AJAX filtering click events on brand flyout links
    const flyoutBrandItems = document.querySelectorAll('.flyout-brand-item');
    flyoutBrandItems.forEach(item => {
        const link = item.querySelector('a');
        if (link) {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                // Set parent category as active
                categoryItems.forEach(i => i.classList.remove('active'));
                const parentCat = item.closest('.category-item');
                if (parentCat) {
                    parentCat.classList.add('active');
                }
                
                // Highlight the active brand item in the sidebar accordion
                const flyoutBrandItems = document.querySelectorAll('.flyout-brand-item');
                flyoutBrandItems.forEach(i => i.classList.remove('selected'));
                item.classList.add('selected');
                
                // Set the custom brand select dropdown to match
                const brandVal = item.dataset.brand;
                const customOptions = document.querySelectorAll('#brand-options-list .custom-option');
                const selectLabel = document.getElementById('brand-select-label');
                
                customOptions.forEach(opt => {
                    opt.classList.remove('selected');
                    if (opt.dataset.value === brandVal) {
                        opt.classList.add('selected');
                        if (selectLabel) {
                            selectLabel.innerText = opt.innerText;
                        }
                    }
                });
                
                filterCatalog();
                updateURLHistory();
            });
        }
    });

    // Handle custom select dropdown interactions for brands
    const selectContainer = document.getElementById('brand-select-container');
    const selectTrigger = document.getElementById('brand-select-trigger');
    const customOptions = document.querySelectorAll('#brand-options-list .custom-option');
    const selectLabel = document.getElementById('brand-select-label');

    if (selectTrigger && selectContainer) {
        selectTrigger.addEventListener('click', (e) => {
            e.stopPropagation();
            selectContainer.classList.toggle('open');
        });

        document.addEventListener('click', () => {
            selectContainer.classList.remove('open');
        });

        customOptions.forEach(opt => {
            opt.addEventListener('click', (e) => {
                e.stopPropagation();
                customOptions.forEach(o => o.classList.remove('selected'));
                opt.classList.add('selected');
                
                if (selectLabel) {
                    selectLabel.innerText = opt.innerText;
                }
                selectContainer.classList.remove('open');
                
                // Sync to flyout brand items in active sidebar category
                const val = opt.dataset.value;
                const flyoutBrandItems = document.querySelectorAll('.flyout-brand-item');
                flyoutBrandItems.forEach(i => {
                    i.classList.remove('selected');
                    if (i.dataset.brand === val) {
                        i.classList.add('selected');
                    }
                });
                
                filterCatalog();
                updateURLHistory();
            });
        });
    }

    function updateURLHistory() {
        if (!searchInput) return; // Only update URL on catalog page
        const activeCategory = document.querySelector('.category-item.active');
        const activeOption = document.querySelector('#brand-options-list .custom-option.selected');
        const searchVal = searchInput.value;
        
        const cat = activeCategory ? activeCategory.dataset.slug : 'all';
        const brand = activeOption ? activeOption.dataset.value : 'all';
        
        let params = [];
        if (cat && cat !== 'all') params.push(`category=${cat}`);
        if (brand && brand !== 'all') params.push(`brand=${brand}`);
        if (searchVal) params.push(`q=${encodeURIComponent(searchVal)}`);
        
        let newURL = window.location.pathname;
        if (params.length > 0) {
            newURL += '?' + params.join('&');
        }
        window.history.pushState({ path: newURL }, '', newURL);
    }

    function filterCatalog() {
        const query = searchInput ? searchInput.value : '';
        const activeCategoryItem = document.querySelector('.category-item.active');
        const categorySlug = activeCategoryItem ? activeCategoryItem.dataset.slug : '';
        const activeOption = document.querySelector('#brand-options-list .custom-option.selected');
        const brandName = activeOption ? activeOption.dataset.value : 'all';
        
        let url = `/catalog/json/?q=${encodeURIComponent(query)}`;
        if (categorySlug && categorySlug !== 'all') {
            url += `&category=${encodeURIComponent(categorySlug)}`;
        }
        if (brandName && brandName !== 'all') {
            url += `&brand=${encodeURIComponent(brandName)}`;
        }
        
        fetch(url)
        .then(res => res.json())
        .then(data => {
            const grid = document.getElementById('products-grid');
            if (!grid) return;
            
            if (data.products.length === 0) {
                grid.innerHTML = `
                    <div style="grid-column: 1 / -1; text-align: center; padding: 60px 0; color: var(--text-muted);">
                        <p style="font-size: 18px; font-weight: 500; margin-bottom: 8px;">No products found</p>
                        <p style="font-size: 14px;">Try adjusting your keywords or category filter.</p>
                    </div>
                `;
                return;
            }
            
            let html = '';
            data.products.forEach(p => {
                html += `
                    <div class="glass-card product-card" style="background: #ffffff; border: 1px solid var(--glass-border); padding: 16px; border-radius: var(--border-radius-sm); position: relative; display: flex; flex-direction: column; justify-content: space-between; min-height: 380px;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                            <span class="stock-badge ${p.stock > 0 ? 'stock-in' : 'stock-out'}" style="font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 2px;">
                                ${p.stock > 0 ? 'IN STOCK' : 'OUT OF STOCK'}
                            </span>
                            ${p.brand ? `<span style="font-size: 10px; font-weight: 800; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px; border: 1px solid #e2e8f0; padding: 1px 5px; border-radius: 2px; background: #f8fafc;">${p.brand}</span>` : ''}
                        </div>
                        <div class="product-img-wrapper" style="text-align: center; margin-bottom: 12px; height: 150px; display: flex; align-items: center; justify-content: center;">
                            <img src="${p.image_url}" alt="${p.name}" class="product-img" style="max-height: 130px; max-width: 100%; object-fit: contain;">
                        </div>
                        <div style="flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between;">
                            <div>
                                <a href="/product/${p.slug}/">
                                    <h3 class="product-title" style="font-size: 13px; font-weight: 700; color: var(--text-primary); line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; height: 54px; margin-bottom: 8px;">${p.name}</h3>
                                </a>
                                <div style="display: flex; align-items: center; gap: 4px; margin-bottom: 12px; color: #fbbf24; font-size: 11px;">
                                    <span>★★★★★</span>
                                    <span style="color: var(--text-muted); font-size: 10.5px; font-weight: 600;">(${parseFloat(p.average_rating).toFixed(1)})</span>
                                </div>
                            </div>
                            <div style="display: flex; align-items: center; justify-content: space-between; padding-top: 10px; border-top: 1px solid #f1f5f9; margin-top: 8px;">
                                <span class="product-price" style="font-size: 15.5px; font-weight: 800; color: var(--text-primary);">$${parseFloat(p.price).toFixed(2)}</span>
                                ${p.stock > 0 ? 
                                  `<button class="btn btn-primary" onclick="addToCart(${p.id})" style="padding: 6px 8px; font-size: 10px; border-radius: 4px; background: #ffffff; border: 1.5px solid #d1d5db; color: #475569; font-weight: 700; white-space: nowrap;" onmouseover="this.style.background='#0b4c8c'; this.style.borderColor='#0b4c8c'; this.style.color='#ffffff';" onmouseout="this.style.background='#ffffff'; this.style.borderColor='#d1d5db'; this.style.color='#475569';">ADD TO CART</button>` : 
                                  `<button class="btn btn-secondary" disabled style="padding: 6px 8px; font-size: 10px; border-radius: 4px; white-space: nowrap;">SOLD OUT</button>`}
                            </div>
                        </div>
                    </div>
                `;
            });
            grid.innerHTML = html;
        });
    }

    // Grid Columns Layout Switcher
    const gridColButtons = document.querySelectorAll('.grid-col-btn');
    const productsGrid = document.getElementById('products-grid');
    if (productsGrid && gridColButtons.length > 0) {
        gridColButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const cols = btn.dataset.cols;
                if (!cols) return;
                
                gridColButtons.forEach(b => {
                    b.classList.remove('active');
                    b.style.background = '#ffffff';
                    b.style.borderColor = '#d1d5db';
                    b.style.color = '#475569';
                });
                btn.classList.add('active');
                btn.style.background = '#16a34a';
                btn.style.borderColor = '#16a34a';
                btn.style.color = '#ffffff';
                
                productsGrid.classList.remove('cols-2', 'cols-3', 'cols-4', 'cols-5');
                productsGrid.classList.add('cols-' + cols);
            });
        });
    }

    // Initialize cart stats
    fetchCartData();
});
