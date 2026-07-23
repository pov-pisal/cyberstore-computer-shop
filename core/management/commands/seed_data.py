from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Category, Product, UserProfile, Coupon, Review

class Command(BaseCommand):
    help = 'Seeds initial database categories, products, and default user accounts.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding initial data...')

        # Clear existing categories and products to avoid orphans
        self.stdout.write('- Clearing existing products and categories...')
        Product.objects.all().delete()
        Category.objects.all().delete()

        # 1. Create Default Users
        self.stdout.write('- Creating user accounts...')
        # Admin / Manager
        if not User.objects.filter(username='admin').exists():
            admin_user = User.objects.create_superuser(
                username='admin',
                email='admin@cyberstore.com',
                password='adminpassword123'
            )
            admin_user.first_name = 'Shop'
            admin_user.last_name = 'Manager'
            admin_user.save()
            
            # Enable manager role in profile
            profile = admin_user.profile
            profile.phone = '+855 12 345 678'
            profile.address = 'Russian Federation Blvd (110), SETEC'
            profile.city = 'Phnom Penh'
            profile.country = 'Cambodia'
            profile.is_manager = True
            profile.save()
            self.stdout.write('  * Created Admin/Manager: admin / adminpassword123')
        else:
            admin_user = User.objects.get(username='admin')
            admin_user.profile.is_manager = True
            admin_user.profile.save()

        # Standard Customer
        if not User.objects.filter(username='customer').exists():
            customer_user = User.objects.create_user(
                username='customer',
                email='customer@gmail.com',
                password='customerpassword123'
            )
            customer_user.first_name = 'Sok'
            customer_user.last_name = 'Dara'
            customer_user.save()
            
            profile = customer_user.profile
            profile.phone = '+855 98 765 432'
            profile.address = 'St 271, Sangkat Boeung Salang'
            profile.city = 'Phnom Penh'
            profile.country = 'Cambodia'
            profile.save()
            self.stdout.write('  * Created Customer: customer / customerpassword123')

        # 2. Create Categories
        self.stdout.write('- Creating product categories...')
        categories_data = [
            {'name': 'CPUs', 'slug': 'cpus', 'description': 'High-performance Central Processing Units.'},
            {'name': 'GPUs', 'slug': 'gpus', 'description': 'Graphics processing units for gaming & rendering.'},
            {'name': 'RAM', 'slug': 'ram', 'description': 'High-speed Random Access Memory modules.'},
            {'name': 'Desktops', 'slug': 'desktops', 'description': 'Custom pre-built desktop towers and workstations.'},
            {'name': 'Laptops', 'slug': 'laptops', 'description': 'Portable powerhouse laptops for gaming and productivity.'},
            {'name': 'Monitors', 'slug': 'monitors', 'description': 'High refresh gaming screens & UHD professional displays.'},
            {'name': 'Accessories', 'slug': 'accessories', 'description': 'Gaming and office peripherals like mice, keyboards, and headsets.'},
            {'name': 'Storage', 'slug': 'storage', 'description': 'Fast SSD storage drives and high-capacity HDDs.'},
        ]
        
        categories = {}
        for cat in categories_data:
            obj, created = Category.objects.get_or_create(
                slug=cat['slug'],
                defaults={'name': cat['name'], 'description': cat['description']}
            )
            categories[cat['slug']] = obj
        self.stdout.write(f'  * Seeded {len(categories_data)} product categories.')

        # 3. Create Products
        self.stdout.write('- Creating computer products...')
        products_data = [
            # --- CPUs ---
            {
                'category': categories['cpus'],
                'name': 'AMD Ryzen 9 7900X CPU',
                'slug': 'amd-ryzen-9-7900x',
                'sku': 'CPU-AMD-R9-7900X',
                'brand': 'AMD',
                'description': '12 Cores and 24 processing threads based on the latest Zen 4 architecture. Reaches boost clocks up to 5.6 GHz.',
                'price': 429.00,
                'stock': 15,
                'specifications': {'Socket': 'Socket AM5', 'Cores': '12', 'Threads': '24', 'Base Clock': '4.7 GHz', 'TDP': '170W'},
                'image_url': 'https://images.unsplash.com/photo-1591488320449-011701bb6704?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['cpus'],
                'name': 'Intel Core i7-13700K CPU',
                'slug': 'intel-core-i7-13700k',
                'sku': 'CPU-INT-I7-13700K',
                'brand': 'Intel',
                'description': '13th Gen Intel Core processor featuring 16 cores (8 Performance cores & 8 Efficient cores). Incredible multitasking power.',
                'price': 369.00,
                'stock': 2,
                'specifications': {'Socket': 'LGA1700', 'Cores': '16', 'Threads': '24', 'Base Clock': '3.4 GHz', 'TDP': '125W'},
                'image_url': 'https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['cpus'],
                'name': 'AMD Ryzen 7 7800X3D CPU',
                'slug': 'amd-ryzen-7-7800x3d',
                'sku': 'CPU-AMD-R7-7800X3D',
                'brand': 'AMD',
                'description': 'Designed specifically for gaming performance with AMD 3D V-Cache technology. 8 cores and 16 threads.',
                'price': 349.00,
                'stock': 12,
                'specifications': {'Socket': 'Socket AM5', 'Cores': '8', 'Threads': '16', 'Base Clock': '4.2 GHz', 'TDP': '120W'},
                'image_url': 'https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['cpus'],
                'name': 'Intel Core i9-14900K CPU',
                'slug': 'intel-core-i9-14900k',
                'sku': 'CPU-INT-I9-14900K',
                'brand': 'Intel',
                'description': 'The ultimate 14th Gen Intel desktop processor. Boasts 24 cores (8P + 16E) reaching speeds up to 6.0 GHz.',
                'price': 529.00,
                'stock': 6,
                'specifications': {'Socket': 'LGA1700', 'Cores': '24', 'Threads': '32', 'Max Clock': '6.0 GHz', 'TDP': '125W'},
                'image_url': 'https://images.unsplash.com/photo-1555680202-c86f0e12f086?q=80&w=300&auto=format&fit=crop'
            },

            # --- GPUs ---
            {
                'category': categories['gpus'],
                'name': 'ASUS ROG Strix RTX 4080 GPU',
                'slug': 'asus-rog-strix-rtx-4080',
                'sku': 'GPU-ASUS-4080-STRIX',
                'brand': 'ASUS',
                'description': 'NVIDIA Ada Lovelace architecture graphics card. Features 16GB GDDR6X VRAM and high-efficiency axial fans.',
                'price': 1199.00,
                'stock': 8,
                'specifications': {'VRAM': '16GB GDDR6X', 'Interface': 'PCIe 4.0 x16', 'Cores': '9728 CUDA', 'Power Connectors': '1x 16-pin'},
                'image_url': 'https://images.unsplash.com/photo-1624705002806-5d72df19c3ad?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['gpus'],
                'name': 'NVIDIA GeForce RTX 4070 Ti Super GPU',
                'slug': 'nvidia-rtx-4070-ti-super',
                'sku': 'GPU-NV-4070TI-SUPER',
                'brand': 'NVIDIA',
                'description': 'Packed with 16GB of fast GDDR6X memory and DLSS 3 frame generation capabilities.',
                'price': 799.00,
                'stock': 9,
                'specifications': {'VRAM': '16GB GDDR6X', 'Interface': 'PCIe 4.0', 'CUDA Cores': '8448', 'Ports': '1x HDMI, 3x DP'},
                'image_url': 'https://images.unsplash.com/photo-1588508065123-287b28e013da?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['gpus'],
                'name': 'AMD Radeon RX 7800 XT GPU',
                'slug': 'amd-radeon-rx-7800-xt',
                'sku': 'GPU-AMD-RX-7800XT',
                'brand': 'AMD',
                'description': 'Engineered on the RDNA 3 chip architecture. Equips 16GB GDDR6 memory to master high-refresh 1440p gaming.',
                'price': 499.00,
                'stock': 14,
                'specifications': {'VRAM': '16GB GDDR6', 'Interface': 'PCIe 4.0', 'Processors': '3840 Stream', 'Ports': '1x HDMI, 3x DP'},
                'image_url': 'https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['gpus'],
                'name': 'MSI RTX 4090 Suprim X GPU',
                'slug': 'msi-rtx-4090-suprim-x',
                'sku': 'GPU-MSI-4090-SUPRIMX',
                'brand': 'MSI',
                'description': 'Ultimate luxury and power. 24GB of GDDR6X VRAM with custom TRI-FROZR 3S cooling system.',
                'price': 1999.00,
                'stock': 3,
                'specifications': {'VRAM': '24GB GDDR6X', 'Interface': 'PCIe 4.0', 'CUDA Cores': '16384', 'TDP': '450W'},
                'image_url': 'https://images.unsplash.com/photo-1591488320449-011701bb6704?q=80&w=300&auto=format&fit=crop'
            },

            # --- RAM ---
            {
                'category': categories['ram'],
                'name': 'Corsair Vengeance 32GB DDR5 RAM',
                'slug': 'corsair-vengeance-32gb-ddr5',
                'sku': 'RAM-CSR-VG-32GB-D5',
                'brand': 'Corsair',
                'description': 'High-performance DDR5 memory optimized for modern motherboards. Frequency clock speed at 6000MHz.',
                'price': 125.00,
                'stock': 25,
                'specifications': {'Capacity': '32GB (2x16GB)', 'Type': 'DDR5', 'Speed': '6000 MHz', 'Latency': 'CL36'},
                'image_url': 'https://images.unsplash.com/photo-1562976540-1502c2145186?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['ram'],
                'name': 'G.Skill Trident Z5 Neo RGB 64GB RAM',
                'slug': 'gskill-trident-z5-64gb',
                'sku': 'RAM-GSK-TZ-64GB-D5',
                'brand': 'G.Skill',
                'description': 'Ultra-fast 64GB DDR5 memory kit with custom programmable RGB lightbar and matte-black heatsinks.',
                'price': 219.00,
                'stock': 10,
                'specifications': {'Capacity': '64GB (2x32GB)', 'Type': 'DDR5', 'Speed': '6000 MHz', 'Latency': 'CL30'},
                'image_url': 'https://images.unsplash.com/photo-1563770660941-20978e870e26?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['ram'],
                'name': 'Kingston FURY Beast 16GB DDR4 RAM',
                'slug': 'kingston-fury-beast-16gb-ddr4',
                'sku': 'RAM-KST-FB-16GB-D4',
                'brand': 'Kingston',
                'description': 'Cost-effective high-performance DDR4 memory upgrade. Auto-overclocking up to 3200MHz.',
                'price': 45.00,
                'stock': 35,
                'specifications': {'Capacity': '16GB (2x8GB)', 'Type': 'DDR4', 'Speed': '3200 MHz', 'Voltage': '1.35V'},
                'image_url': 'https://images.unsplash.com/photo-1541029071515-84cc54f84dc5?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['ram'],
                'name': 'Teamgroup Delta RGB 32GB DDR5',
                'slug': 'teamgroup-delta-32gb-ddr5',
                'sku': 'RAM-TMG-DL-32GB-D5',
                'brand': 'Teamgroup',
                'description': '120-degree ultra-wide angle RGB lighting DDR5 module, clocked at 6400MHz with custom cooling spreaders.',
                'price': 139.00,
                'stock': 15,
                'specifications': {'Capacity': '32GB (2x16GB)', 'Type': 'DDR5', 'Speed': '6400 MHz', 'Latency': 'CL32'},
                'image_url': 'https://images.unsplash.com/photo-1563770660941-20978e870e26?q=80&w=300&auto=format&fit=crop'
            },

            # --- Desktops ---
            {
                'category': categories['desktops'],
                'name': 'MSI Aegis RS Gaming Desktop',
                'slug': 'msi-aegis-rs-desktop',
                'sku': 'DKT-MSI-AEGIS-RS',
                'brand': 'MSI',
                'description': 'Built for high framerate gaming. Houses Intel Core i7 processor, RTX 4070 Ti, and 2TB NVMe SSD.',
                'price': 1899.00,
                'stock': 4,
                'specifications': {'Processor': 'Intel i7-13700KF', 'Graphics': 'RTX 4070 Ti', 'Memory': '32GB DDR5', 'Storage': '2TB SSD', 'OS': 'Windows 11'},
                'image_url': 'https://images.unsplash.com/photo-1587831990711-23ca6441447b?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['desktops'],
                'name': 'DELL Alienware Aurora R16 Desktop',
                'slug': 'dell-alienware-aurora-r16',
                'sku': 'DKT-DELL-AW-R16',
                'brand': 'DELL',
                'description': 'Ultimate gaming performance desktop from Alienware. Liquid cooled i7 with RTX 4070 graphics.',
                'price': 1899.00,
                'stock': 3,
                'specifications': {'Processor': 'Intel i7-13700F', 'Graphics': 'RTX 4070 12GB', 'Memory': '32GB DDR5', 'Storage': '1TB SSD'},
                'image_url': 'https://images.unsplash.com/photo-1618424181497-157f25b6ddd5?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['desktops'],
                'name': 'Origin PC Millennium Workstation',
                'slug': 'origin-pc-millennium-workstation',
                'sku': 'DKT-ORIGIN-MILLENNIUM',
                'brand': 'Origin PC',
                'description': 'A monolithic workspace powerhouse configured with a 24-Core AMD Threadripper CPU and dual RTX 4090 graphics cards.',
                'price': 4299.00,
                'stock': 2,
                'specifications': {'Processor': 'Threadripper 7960X', 'Graphics': '2x RTX 4090 SLI', 'Memory': '128GB DDR5', 'Storage': '4TB SSD'},
                'image_url': 'https://images.unsplash.com/photo-1547082299-de196ea013d6?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['desktops'],
                'name': 'Apple Mac Studio M2 Max',
                'slug': 'apple-mac-studio-m2-max',
                'sku': 'DKT-APP-STUDIO-M2',
                'brand': 'Apple',
                'description': 'Compact desktop workstation with massive processing bandwidth. Outfitted with Apple M2 Max chip.',
                'price': 1999.00,
                'stock': 5,
                'specifications': {'Processor': 'Apple M2 Max (12-Core)', 'Graphics': '30-Core GPU', 'Unified Memory': '32GB', 'Storage': '512GB SSD'},
                'image_url': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?q=80&w=300&auto=format&fit=crop'
            },

            # --- Laptops ---
            {
                'category': categories['laptops'],
                'name': 'ASUS ROG Zephyrus G14 Laptop',
                'slug': 'asus-rog-zephyrus-g14',
                'sku': 'LPT-ASUS-ROG-Z-G14',
                'brand': 'ASUS',
                'description': 'Compact and lightweight 14-inch gaming laptop. Features QHD+ 165Hz display and GeForce RTX 4060 graphics.',
                'price': 1499.00,
                'stock': 5,
                'specifications': {'Display': '14" QHD+ 165Hz', 'Processor': 'AMD Ryzen 9 7940HS', 'Graphics': 'RTX 4060', 'Memory': '16GB', 'Storage': '1TB SSD'},
                'image_url': 'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['laptops'],
                'name': 'Lenovo Legion Pro 5i Laptop',
                'slug': 'lenovo-legion-pro-5i',
                'sku': 'LPT-LNV-LEGION-5I',
                'brand': 'Lenovo',
                'description': 'Pro-grade gaming notebook with massive 16-inch high refresh display and GeForce RTX 4070 graphics.',
                'price': 1399.00,
                'stock': 7,
                'specifications': {'Display': '16" WQXGA 240Hz', 'Processor': 'Intel i7-13700HX', 'Graphics': 'RTX 4070', 'Memory': '32GB', 'Storage': '1TB SSD'},
                'image_url': 'https://images.unsplash.com/photo-1603302576837-37561b2e2302?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['laptops'],
                'name': 'Apple MacBook Pro 16" M3 Max Laptop',
                'slug': 'apple-macbook-pro-16-m3-max',
                'sku': 'LPT-APP-MBP16-M3MAX',
                'brand': 'Apple',
                'description': 'Portable workstation built with the M3 Max custom chip. Runs demanding video pipelines and ML compilations.',
                'price': 3499.00,
                'stock': 4,
                'specifications': {'Display': '16.2" Retina XDR 120Hz', 'Processor': 'Apple M3 Max', 'Memory': '48GB Unified', 'Storage': '1TB SSD'},
                'image_url': 'https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['laptops'],
                'name': 'DELL XPS 15 9530 Creator Laptop',
                'slug': 'dell-xps-15-9530',
                'sku': 'LPT-DELL-XPS-15',
                'brand': 'DELL',
                'description': 'Premium thin-and-light laptop for creators. OLED touch display, Intel i9 CPU, and RTX 4060 GPU.',
                'price': 2299.00,
                'stock': 6,
                'specifications': {'Display': '15.6" OLED 3.5K Touch', 'Processor': 'Intel i9-13900H', 'Graphics': 'RTX 4060', 'Memory': '32GB', 'Storage': '1TB SSD'},
                'image_url': 'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?q=80&w=300&auto=format&fit=crop'
            },

            # --- Monitors ---
            {
                'category': categories['monitors'],
                'name': 'ASUS ROG Swift PG32UQX Monitor',
                'slug': 'asus-rog-swift-pg32uqx',
                'sku': 'MON-ASUS-PG32UQX',
                'brand': 'ASUS',
                'description': '32-inch 4K HDR gaming monitor with Mini-LED backlighting, G-Sync Ultimate, and 144Hz refresh rate.',
                'price': 2499.00,
                'stock': 4,
                'specifications': {'Size': '32-inch', 'Resolution': '4K UHD (3840x2160)', 'Refresh Rate': '144Hz', 'Panel Type': 'IPS Mini-LED'},
                'image_url': 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['monitors'],
                'name': 'DELL UltraSharp U2723QE 4K Monitor',
                'slug': 'dell-ultrasharp-u2723qe',
                'sku': 'MON-DELL-U2723QE',
                'brand': 'DELL',
                'description': '27-inch 4K USB-C Hub monitor with IPS Black technology for double the contrast ratio and 98% DCI-P3 color.',
                'price': 579.00,
                'stock': 12,
                'specifications': {'Size': '27-inch', 'Resolution': '4K UHD', 'Refresh Rate': '60Hz', 'Panel Type': 'IPS Black', 'Ports': 'USB-C DP'},
                'image_url': 'https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['monitors'],
                'name': 'LG UltraGear 27GP850-B Monitor',
                'slug': 'lg-ultragear-27gp850b',
                'sku': 'MON-LG-27GP850B',
                'brand': 'LG',
                'description': '27-inch QHD Nano IPS gaming monitor with 1ms response time, 165Hz refresh rate (OC 180Hz), and G-Sync compatibility.',
                'price': 349.00,
                'stock': 18,
                'specifications': {'Size': '27-inch', 'Resolution': 'QHD (2560x1440)', 'Refresh Rate': '180Hz (OC)', 'Response Time': '1ms'},
                'image_url': 'https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['monitors'],
                'name': 'Samsung Odyssey G9 Curved Monitor',
                'slug': 'samsung-odyssey-g9',
                'sku': 'MON-SAM-G9-CURVED',
                'brand': 'Samsung',
                'description': '49-inch super ultra-wide 1000R curved gaming monitor with Dual QHD resolution, 240Hz refresh, and 1ms response.',
                'price': 1299.00,
                'stock': 3,
                'specifications': {'Size': '49-inch Super Ultrawide', 'Curvature': '1000R', 'Resolution': '5120x1440', 'Refresh Rate': '240Hz'},
                'image_url': 'https://images.unsplash.com/photo-1616763355548-1b606f439f86?q=80&w=300&auto=format&fit=crop'
            },

            # --- Accessories ---
            {
                'category': categories['accessories'],
                'name': 'Logitech G Pro X Superlight Mouse',
                'slug': 'logitech-g-pro-x-superlight',
                'sku': 'ACC-LOG-GPXS-MOUSE',
                'brand': 'Logitech',
                'description': 'Ultra-lightweight wireless gaming mouse designed for esports professionals. Weighs less than 63 grams.',
                'price': 129.00,
                'stock': 30,
                'specifications': {'Weight': '< 63g', 'Sensor': 'HERO 25K', 'Connectivity': 'LIGHTSPEED Wireless', 'Battery Life': '70h'},
                'image_url': 'https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['accessories'],
                'name': 'Razer BlackWidow V4 Pro Keyboard',
                'slug': 'razer-blackwidow-v4-pro',
                'sku': 'ACC-RZR-BWV4-KB',
                'brand': 'Razer',
                'description': 'Full-blown mechanical gaming keyboard with Razer Green clicky switches, underglow RGB, and dedicated macro keys.',
                'price': 229.00,
                'stock': 15,
                'specifications': {'Switches': 'Razer Green Mechanical', 'Layout': 'Full Size', 'RGB': 'Chroma Per-key', 'Macros': '8 Dedicated'},
                'image_url': 'https://images.unsplash.com/photo-1601445638532-3c6f6c3aa1d6?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['accessories'],
                'name': 'Corsair HS80 RGB Wireless Headset',
                'slug': 'corsair-hs80-rgb-wireless',
                'sku': 'ACC-CSR-HS80-HEADSET',
                'brand': 'Corsair',
                'description': 'Premium gaming headset with SLIPSTREAM wireless audio, broadcast-grade omnidirectional microphone, and Dolby Atmos support.',
                'price': 149.00,
                'stock': 20,
                'specifications': {'Audio': 'Dolby Atmos Spatial', 'Driver': '50mm Neodymium', 'Frequency': '20Hz-40kHz', 'Wireless': 'SLIPSTREAM'},
                'image_url': 'https://images.unsplash.com/photo-1618384887929-16ec33fab9ef?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['accessories'],
                'name': 'Logitech MX Master 3S Mouse',
                'slug': 'logitech-mx-master-3s',
                'sku': 'ACC-LOG-MX3S-MOUSE',
                'brand': 'Logitech',
                'description': 'Ergonomic office productivity mouse with MagSpeed electromagnetic scrolling and quiet click switches.',
                'price': 99.00,
                'stock': 40,
                'specifications': {'Sensor': '8K DPI Darkfield', 'Buttons': '7 Programmable', 'Scrolling': 'MagSpeed Metal Wheel', 'Battery': '70 days'},
                'image_url': 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?q=80&w=300&auto=format&fit=crop'
            },

            # --- Storage ---
            {
                'category': categories['storage'],
                'name': 'Samsung 990 PRO 2TB NVMe SSD',
                'slug': 'samsung-990-pro-2tb',
                'sku': 'STG-SAM-990P-2TB',
                'brand': 'Samsung',
                'description': 'PCIe Gen4 solid state drive delivering peak sequential read speeds up to 7450 MB/s for PC hardware enthusiasts.',
                'price': 179.00,
                'stock': 25,
                'specifications': {'Capacity': '2TB', 'Interface': 'PCIe Gen4.0 x4 NVMe', 'Read Speed': 'Up to 7450 MB/s', 'Write Speed': 'Up to 6900 MB/s'},
                'image_url': 'https://images.unsplash.com/photo-1531403009284-440f080d1e12?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['storage'],
                'name': 'Crucial T700 1TB PCIe 5.0 SSD',
                'slug': 'crucial-t700-1tb-pcie5',
                'sku': 'STG-CRL-T700-1TB',
                'brand': 'Crucial',
                'description': 'Next-gen PCIe 5.0 NVMe SSD boasting record speeds up to 12400 MB/s. Prepared for DirectStorage configurations.',
                'price': 169.00,
                'stock': 8,
                'specifications': {'Capacity': '1TB', 'Interface': 'PCIe Gen5.0 x4 NVMe', 'Read Speed': 'Up to 11700 MB/s', 'Write Speed': 'Up to 9500 MB/s'},
                'image_url': 'https://images.unsplash.com/photo-1597852074816-d933c7d2b988?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['storage'],
                'name': 'WD Black SN850X 2TB NVMe SSD',
                'slug': 'wd-black-sn850x-2tb',
                'sku': 'STG-WDB-SN850X-2TB',
                'brand': 'WD',
                'description': 'Premium high-speed gaming SSD with optional heatsink. Delivers read speeds up to 7300 MB/s.',
                'price': 159.00,
                'stock': 18,
                'specifications': {'Capacity': '2TB', 'Interface': 'PCIe Gen4 x4', 'Read Speed': '7300 MB/s', 'Form Factor': 'M.2 2280'},
                'image_url': 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?q=80&w=300&auto=format&fit=crop'
            },
            {
                'category': categories['storage'],
                'name': 'Samsung T7 Shield 2TB Portable SSD',
                'slug': 'samsung-t7-shield-2tb',
                'sku': 'STG-SAM-T7S-2TB',
                'brand': 'Samsung',
                'description': 'Super durable portable solid state drive with IP65 water/dust resistance and 1050 MB/s transfer speeds.',
                'price': 149.00,
                'stock': 22,
                'specifications': {'Capacity': '2TB', 'Interface': 'USB 3.2 Gen2', 'Read Speed': '1050 MB/s', 'Protection': 'IP65 Rated'},
                'image_url': 'https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?q=80&w=300&auto=format&fit=crop'
            }
        ]

        for prod in products_data:
            Product.objects.update_or_create(
                slug=prod['slug'],
                defaults={
                    'category': prod['category'],
                    'name': prod['name'],
                    'sku': prod['sku'],
                    'brand': prod['brand'],
                    'description': prod['description'],
                    'price': prod['price'],
                    'stock': prod['stock'],
                    'specifications': prod['specifications'],
                    'image_url': prod['image_url']
                }
            )
        # Seed Coupons
        self.stdout.write('- Seeding coupons...')
        coupons = [
            {'code': 'CYBERGPU', 'discount_percent': 10},
            {'code': 'CYBER10', 'discount_percent': 10},
            {'code': 'WELCOME15', 'discount_percent': 15},
        ]
        for c in coupons:
            Coupon.objects.update_or_create(code=c['code'], defaults={'discount_percent': c['discount_percent'], 'is_active': True})

        # Seed reviews
        self.stdout.write('- Seeding product reviews...')
        customer_user = User.objects.filter(username='customer').first()
        admin_user = User.objects.filter(username='admin').first()
        
        if customer_user and admin_user:
            p1 = Product.objects.filter(slug='amd-ryzen-7-7800x3d').first()
            if p1:
                Review.objects.update_or_create(product=p1, user=customer_user, defaults={'rating': 5, 'comment': "Best gaming CPU on the market! Low TDP and insane performance."})
                Review.objects.update_or_create(product=p1, user=admin_user, defaults={'rating': 5, 'comment': "Highly recommended. Runs cool and delivers top-tier 1% low framerates."})
                
            p2 = Product.objects.filter(slug='msi-rtx-4090-suprim-x').first()
            if p2:
                Review.objects.update_or_create(product=p2, user=customer_user, defaults={'rating': 5, 'comment': "Absolute monster of a card! A bit expensive but completely worth the rendering speeds."})
                
            p3 = Product.objects.filter(slug='dell-alienware-aurora-r16').first()
            if p3:
                Review.objects.update_or_create(product=p3, user=customer_user, defaults={'rating': 4, 'comment': "Super clean desktop. Quiet cooling. Wish it had a bit more expansion slots."})

        self.stdout.write('Successfully seeded database!')
