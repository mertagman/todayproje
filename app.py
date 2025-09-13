from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_from_directory
from functools import wraps
import sqlite3
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from database import init_db, get_db_connection

app = Flask(__name__,
            static_folder="static", static_url_path='')
app.secret_key = 'todyprj'

# File upload configuration
UPLOAD_FOLDER = 'user_custom_upload'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database on startup
init_db()

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file):
    """Save uploaded file with unique name and return the path"""
    if file and allowed_file(file.filename):
        # Create unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{timestamp}.{extension}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filepath
    return None

def parse_price(price_str):
    """Parse formatted price string (e.g., '5.950.000') to float"""
    if not price_str:
        return None
    # Remove dots and convert to float
    clean_price = price_str.replace('.', '')
    try:
        return float(clean_price)
    except ValueError:
        return None

def format_price_display(price):
    """Format price for display with Turkish formatting"""
    if not price:
        return None
    return '{:,.0f}'.format(price).replace(',', '.')

# Add template filter for price formatting
app.jinja_env.filters['format_price'] = format_price_display

# Language management
def get_language():
    """Get current language from session, default to Turkish"""
    return session.get('language', 'tr')

def set_language(lang):
    """Set language in session"""
    session['language'] = lang

# Language texts mapping
LANGUAGE_TEXTS = {
    'tr': {
        'home': 'Anasayfa',
        'about': 'Hakkımızda',
        'advertisements': 'İlanlar',
        'for_sale': 'Satılık',
        'for_rent': 'Kiralık',
        'contact': 'İLETİŞİM',
        'turkish': 'Türkçe',
        'english': 'English',
        'arabic': 'عربي',
        'call_us': 'Bizi Arayın',
        'email': 'Email',
        'quick_menu': 'Hızlı Menü',
        'for_sale_ads': 'Satılık İlanlar',
        'for_rent_ads': 'Kiralık İlanlar',
        'we_are_here': 'Sizin İçin Buradayız',
        'we_offer_services': 'Herkes için uygun hizmetler sunuyoruz',
        'all_rights_reserved': '© 2025 Today Proje Gayrimenkul | Tüm Hakları Saklıdır.',
        'search': 'Ara...',
        'search_placeholder': 'Ara...',
        'investment_advisor': 'Yatırım Danışmanınız',
        'help_evaluate_investments': 'Yatırımlarınızı değerlendirmenize yardımcı oluyoruz',
        'real_estate_consulting': 'Gayrimenkul Danışmanlık',
        'popular_ads': 'Popüler İlanlar',
        'recommended_ads': 'Önerilen İlanlar',
        'view_details': 'Detayları Görüntüle',
        'price': 'Fiyat',
        'views': 'Görüntülenme',
        'gold_ad': 'Altın İlan',
        'view_all': 'Tümünü Gör',
        'suitable_consulting': 'Uygun Danışmalık',
        'suitable_consulting_desc': 'Uygun danışmalık hizmeti sunuyoruz',
        'quick_support': 'Hızlı Destek',
        'quick_support_desc': 'Bir telefon uzağınızdayız',
        'investment_needs': 'Yatırım İhtiyaçlarınız İçin',
        'contact_us': 'Bizimle iletişime geçin',
        'monthly': 'Aylık',
        'about_us': 'Hakkımızda',
        'about_description': 'Gayrimenkul sektöründe uzmanlaşmış bir reklam ve danışmanlık ajansıyız. Müşterilerimize, modern pazarlama stratejileri ve yenilikçi çözümler sunarak gayrimenkul projelerini en etkili şekilde tanıtmalarına yardımcı oluyoruz. Deneyimli ekibimiz, sektörün dinamiklerini yakından takip ederek, markalarınıza değer katacak yaratıcı ve sonuç odaklı kampanyalar geliştirir. Amacımız, sadece bir hizmet sağlayıcı değil, müşterilerimizin güvenilir bir iş ortağı olarak onların başarılarına katkıda bulunmaktır.',
        'our_vision': 'Vizyonumuz',
        'vision_description': 'Gayrimenkul sektöründe, reklam ve danışmanlık hizmetlerinde fark yaratan, inovatif çözümler sunan ve sektördeki dönüşümlere öncülük eden lider bir marka olmak. Müşterilerimizin hedeflerine ulaşmalarını sağlayarak, sektördeki en güvenilir ve tercih edilen iş ortağı olarak konumlanmak.',
        'our_mission': 'Misyonumuz',
        'mission_description': 'Müşterilerimize, gayrimenkul sektöründe rekabet avantajı sağlayacak yaratıcı ve etkili pazarlama çözümleri sunmak. Her projede maksimum verimliliği ve başarıyı hedefleyerek, müşteri memnuniyetini en üst düzeyde tutmak. Yenilikçi yaklaşımlarımızla sektöre değer katmak ve müşterilerimizin uzun vadeli başarılarına katkıda bulunmak.',
        'for_sale_ads': 'Satılık İlanlar',
        'for_rent_ads': 'Kiralık İlanlar',
        'contract_number': 'Sözleşme No',
        'contract_number_placeholder': 'Sözleşme numarasını girin...',
        'search_button': 'Ara',
        'price_not_specified': 'Fiyat Belirtilmemiş',
        'click_for_details': 'Detaylar için tıklayın...',
        'view_details': 'Detayı Gör',
        'no_results_found': 'için sonuç bulunamadı',
        'no_ads_yet': 'Henüz ilan bulunmuyor',
        'try_different_contract': 'Farklı bir sözleşme numarası ile tekrar deneyin.',
        'new_ads_coming_soon': 'Yakında yeni ilanlar eklenecektir.',
        'view_all_ads': 'Tüm İlanları Gör',
        'room_type': 'Oda Tipi',
        'ad_type': 'İlan Tipi',
        'not_specified': 'Belirtilmemiş',
        'ad_details': 'İlan Detayı',
        'contact_for_details': 'Detaylı bilgi için iletişime geçiniz.',
        'photos': 'Fotoğraflar',
        'rent_price': 'Kira Fiyatı',
        'sale_price': 'Satış Fiyatı',
        'monthly_rent': 'Aylık',
        'contact': 'İletişim',
        'phone': 'Telefon',
        'address': 'Adres',
        'view_on_google_maps': 'Google Haritada Gör'
    },
    'en': {
        'home': 'Home',
        'about': 'About Us',
        'advertisements': 'Advertisements',
        'for_sale': 'For Sale',
        'for_rent': 'For Rent',
        'contact': 'Contact',
        'turkish': 'Türkçe',
        'english': 'English',
        'arabic': 'عربي',
        'call_us': 'Call Us',
        'email': 'Email',
        'quick_menu': 'Quick Menu',
        'for_sale_ads': 'For Sale Ads',
        'for_rent_ads': 'For Rent Ads',
        'we_are_here': 'We Are Here For You',
        'we_offer_services': 'We offer services suitable for everyone',
        'all_rights_reserved': '© 2025 Today Proje Gayrimenkul | All Rights Reserved.',
        'search': 'Search...',
        'search_placeholder': 'Search...',
        'investment_advisor': 'Your Investment Advisor',
        'help_evaluate_investments': 'We help you evaluate your investments',
        'real_estate_consulting': 'Real Estate Consulting',
        'popular_ads': 'Popular Advertisements',
        'recommended_ads': 'Recommended Advertisements',
        'view_details': 'View Details',
        'price': 'Price',
        'views': 'Views',
        'gold_ad': 'Gold Advertisement',
        'view_all': 'View All',
        'suitable_consulting': 'Suitable Consulting',
        'suitable_consulting_desc': 'We provide suitable consulting services',
        'quick_support': 'Quick Support',
        'quick_support_desc': 'We are just a phone call away',
        'investment_needs': 'For Your Investment Needs',
        'contact_us': 'Contact Us',
        'monthly': 'Monthly',
        'about_us': 'About Us',
        'about_description': 'We are an advertising and consulting agency specialized in the real estate sector. We help our clients promote their real estate projects in the most effective way by offering modern marketing strategies and innovative solutions. Our experienced team closely follows the dynamics of the sector and develops creative and result-oriented campaigns that will add value to your brands. Our goal is not only to be a service provider, but to contribute to the success of our clients as their trusted business partner.',
        'our_vision': 'Our Vision',
        'vision_description': 'To be a leading brand in the real estate sector that makes a difference in advertising and consulting services, offers innovative solutions and leads the transformations in the sector. To position ourselves as the most reliable and preferred business partner in the sector by enabling our clients to achieve their goals.',
        'our_mission': 'Our Mission',
        'mission_description': 'To provide our clients with creative and effective marketing solutions that will provide competitive advantage in the real estate sector. To keep customer satisfaction at the highest level by targeting maximum efficiency and success in every project. To add value to the sector with our innovative approaches and contribute to the long-term success of our clients.',
        'for_sale_ads': 'For Sale Advertisements',
        'for_rent_ads': 'For Rent Advertisements',
        'contract_number': 'Contract Number',
        'contract_number_placeholder': 'Enter contract number...',
        'search_button': 'Search',
        'price_not_specified': 'Price Not Specified',
        'click_for_details': 'Click for details...',
        'view_details': 'View Details',
        'no_results_found': 'no results found for',
        'no_ads_yet': 'No advertisements yet',
        'try_different_contract': 'Try with a different contract number.',
        'new_ads_coming_soon': 'New advertisements will be added soon.',
        'view_all_ads': 'View All Advertisements',
        'room_type': 'Room Type',
        'ad_type': 'Advertisement Type',
        'not_specified': 'Not Specified',
        'ad_details': 'Advertisement Details',
        'contact_for_details': 'Contact for detailed information.',
        'photos': 'Photos',
        'rent_price': 'Rent Price',
        'sale_price': 'Sale Price',
        'monthly_rent': 'Monthly',
        'contact': 'Contact',
        'phone': 'Phone',
        'address': 'Address',
        'view_on_google_maps': 'View on Google Maps'
    },
    'ar': {
        'home': 'الرئيسية',
        'about': 'من نحن',
        'advertisements': 'الإعلانات',
        'for_sale': 'للبيع',
        'for_rent': 'للإيجار',
        'contact': 'اتصل بنا',
        'turkish': 'Türkçe',
        'english': 'English',
        'arabic': 'عربي',
        'call_us': 'اتصل بنا',
        'email': 'البريد الإلكتروني',
        'quick_menu': 'القائمة السريعة',
        'for_sale_ads': 'إعلانات للبيع',
        'for_rent_ads': 'إعلانات للإيجار',
        'we_are_here': 'نحن هنا من أجلك',
        'we_offer_services': 'نحن نقدم خدمات مناسبة للجميع',
        'all_rights_reserved': '© 2025 Today Proje Gayrimenkul | جميع الحقوق محفوظة.',
        'search': 'بحث...',
        'search_placeholder': 'بحث...',
        'investment_advisor': 'مستشار الاستثمار الخاص بك',
        'help_evaluate_investments': 'نساعدك في تقييم استثماراتك',
        'real_estate_consulting': 'استشارات العقارات',
        'popular_ads': 'الإعلانات الشائعة',
        'recommended_ads': 'الإعلانات الموصى بها',
        'view_details': 'عرض التفاصيل',
        'price': 'السعر',
        'views': 'المشاهدات',
        'gold_ad': 'إعلان ذهبي',
        'view_all': 'عرض الكل',
        'suitable_consulting': 'استشارات مناسبة',
        'suitable_consulting_desc': 'نقدم خدمات استشارية مناسبة',
        'quick_support': 'دعم سريع',
        'quick_support_desc': 'نحن على بُعد مكالمة هاتفية',
        'investment_needs': 'لاحتياجاتك الاستثمارية',
        'contact_us': 'تواصل معنا',
        'monthly': 'شهرياً',
        'about_us': 'من نحن',
        'about_description': 'نحن وكالة إعلانية واستشارية متخصصة في قطاع العقارات. نساعد عملائنا في الترويج لمشاريعهم العقارية بأكثر الطرق فعالية من خلال تقديم استراتيجيات التسويق الحديثة والحلول المبتكرة. فريقنا ذو الخبرة يتابع عن كثب ديناميكيات القطاع ويطور حملات إبداعية وموجهة للنتائج تضيف قيمة لعلاماتكم التجارية. هدفنا ليس فقط أن نكون مقدم خدمة، بل أن نساهم في نجاح عملائنا كشريك أعمال موثوق.',
        'our_vision': 'رؤيتنا',
        'vision_description': 'أن نكون علامة تجارية رائدة في قطاع العقارات تخلق فرقاً في خدمات الإعلان والاستشارات، وتقدم حلولاً مبتكرة وتقود التحولات في القطاع. أن نركز أنفسنا كشريك أعمال الأكثر موثوقية وتفضيلاً في القطاع من خلال تمكين عملائنا من تحقيق أهدافهم.',
        'our_mission': 'مهمتنا',
        'mission_description': 'تزويد عملائنا بحلول تسويقية إبداعية وفعالة توفر ميزة تنافسية في قطاع العقارات. الحفاظ على رضا العملاء في أعلى مستوى من خلال استهداف أقصى كفاءة ونجاح في كل مشروع. إضافة قيمة للقطاع بمناهجنا المبتكرة والمساهمة في النجاح طويل المدى لعملائنا.',
        'for_sale_ads': 'إعلانات للبيع',
        'for_rent_ads': 'إعلانات للإيجار',
        'contract_number': 'رقم العقد',
        'contract_number_placeholder': 'أدخل رقم العقد...',
        'search_button': 'بحث',
        'price_not_specified': 'السعر غير محدد',
        'click_for_details': 'انقر للتفاصيل...',
        'view_details': 'عرض التفاصيل',
        'no_results_found': 'لم يتم العثور على نتائج لـ',
        'no_ads_yet': 'لا توجد إعلانات بعد',
        'try_different_contract': 'جرب برقم عقد مختلف.',
        'new_ads_coming_soon': 'سيتم إضافة إعلانات جديدة قريباً.',
        'view_all_ads': 'عرض جميع الإعلانات',
        'room_type': 'نوع الغرفة',
        'ad_type': 'نوع الإعلان',
        'not_specified': 'غير محدد',
        'ad_details': 'تفاصيل الإعلان',
        'contact_for_details': 'تواصل للحصول على معلومات مفصلة.',
        'photos': 'الصور',
        'rent_price': 'سعر الإيجار',
        'sale_price': 'سعر البيع',
        'monthly_rent': 'شهرياً',
        'contact': 'اتصل بنا',
        'phone': 'الهاتف',
        'address': 'العنوان',
        'view_on_google_maps': 'عرض على خرائط جوجل'
    }
}

def get_text(key):
    """Get text for current language"""
    lang = get_language()
    return LANGUAGE_TEXTS.get(lang, LANGUAGE_TEXTS['tr']).get(key, key)

# Add template context processor
@app.context_processor
def inject_language():
    return {
        'current_language': get_language(),
        'get_text': get_text
    }

# Static admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'today2025!*'

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    conn = get_db_connection()
    
    # Get popular advertisements (highest views, max 5)
    popular_ads = conn.execute('''
        SELECT id, title, advertisement_type, img_1, sale_price, rent_price, view, is_gold
        FROM ilanlar 
        WHERE status = 1 
        ORDER BY view DESC 
        LIMIT 5
    ''').fetchall()
    
    # Get recommended advertisements (newest, max 5)
    recommended_ads = conn.execute('''
        SELECT id, title, advertisement_type, img_1, sale_price, rent_price, view, is_gold
        FROM ilanlar 
        WHERE status = 1 
        ORDER BY creation_date DESC 
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template('index.html', popular_ads=popular_ads, recommended_ads=recommended_ads)

@app.route('/hakkimizda')
def hakkimizda():
    return render_template('about.html')

@app.route('/iletisim')
def iletisim():
    return render_template('iletisim.html')

@app.route('/set_language/<lang>')
def set_language_route(lang):
    """Set language and redirect back to previous page or home"""
    if lang in ['tr', 'en', 'ar']:
        set_language(lang)
        
    # Redirect back to the page they came from or home
    return redirect(request.referrer or url_for('index'))

@app.route('/ilanlar')
def ilanlar():
    # Get page number from query parameters (default to 1)
    page = request.args.get('page', 1, type=int)
    # Get search query from query parameters
    search_query = request.args.get('search', '', type=str)
    # Get price type query (satilik/kiralik, default to satilik)
    price_type = request.args.get('price_type', 'satilik', type=str)
    
    # Items per page
    per_page = 8
    offset = (page - 1) * per_page
    
    conn = get_db_connection()
    
    # Build the SQL query based on search
    if search_query:
        # Search by contract_id
        count_query = '''
            SELECT COUNT(*) as total 
            FROM ilanlar 
            WHERE status = 1 AND contract_id LIKE ?
        '''
        ads_query = '''
            SELECT id, title, advertisement_type, img_1, sale_price, rent_price, 
                   view, is_gold, contract_id, adres, bed_type, description
            FROM ilanlar 
            WHERE status = 1 AND contract_id LIKE ?
            ORDER BY creation_date DESC 
            LIMIT ? OFFSET ?
        '''
        search_param = f'%{search_query}%'
        
        # Get total count for pagination
        total_count = conn.execute(count_query, (search_param,)).fetchone()['total']
        
        # Get advertisements
        advertisements = conn.execute(ads_query, (search_param, per_page, offset)).fetchall()
    else:
        # No search, get all active advertisements
        count_query = '''
            SELECT COUNT(*) as total 
            FROM ilanlar 
            WHERE status = 1
        '''
        ads_query = '''
            SELECT id, title, advertisement_type, img_1, sale_price, rent_price, 
                   view, is_gold, contract_id, adres, bed_type, description
            FROM ilanlar 
            WHERE status = 1 
            ORDER BY creation_date DESC 
            LIMIT ? OFFSET ?
        '''
        
        # Get total count for pagination
        total_count = conn.execute(count_query).fetchone()['total']
        
        # Get advertisements
        advertisements = conn.execute(ads_query, (per_page, offset)).fetchall()
    
    conn.close()
    
    # Calculate pagination info
    total_pages = (total_count + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    return render_template('ilanlar.html', 
                         advertisements=advertisements,
                         page=page,
                         total_pages=total_pages,
                         has_prev=has_prev,
                         has_next=has_next,
                         search_query=search_query,
                         price_type=price_type,
                         total_count=total_count)

@app.route('/ilanlar/<id>')
def ilan_detay(id):
    # Get price type query (satilik/kiralik, default to satilik)
    price_type = request.args.get('price_type', 'satilik', type=str)
    
    conn = get_db_connection()
    
    # Get advertisement by ID
    advertisement = conn.execute('''
        SELECT * FROM ilanlar WHERE id = ? AND status = 1
    ''', (id,)).fetchone()
    
    conn.close()
    
    if not advertisement:
        flash('İlan bulunamadı!', 'error')
        return redirect(url_for('ilanlar'))
    
    # Increment view count
    conn = get_db_connection()
    conn.execute('''
        UPDATE ilanlar SET view = view + 1 WHERE id = ?
    ''', (id,))
    conn.commit()
    conn.close()
    
    return render_template('ilan_detay.html', advertisement=advertisement, price_type=price_type)

# Admin routes
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password!', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('You have been logged out!', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin')
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/api/advertisements')
@login_required
def api_advertisements():
    """API endpoint for DataTables to fetch advertisements"""
    conn = get_db_connection()
    advertisements = conn.execute('''
        SELECT id, title, advertisement_type, adres, view, is_gold, img_1, img_2, img_3,
               sale_price, rent_price, contract_id, description, description_en, 
               description_ar, deed, bed_type, status, creation_date, update_date
        FROM ilanlar 
        ORDER BY creation_date DESC
    ''').fetchall()
    conn.close()
    
    # Convert to list of dictionaries for JSON response
    data = []
    for ad in advertisements:
        data.append({
            'id': ad['id'],
            'title': ad['title'],
            'advertisement_type': ad['advertisement_type'],
            'adres': ad['adres'],
            'view': ad['view'],
            'is_gold': bool(ad['is_gold']),
            'img_1': ad['img_1'],
            'img_2': ad['img_2'],
            'img_3': ad['img_3'],
            'sale_price': ad['sale_price'],
            'rent_price': ad['rent_price'],
            'contract_id': ad['contract_id'],
            'description': ad['description'],
            'description_en': ad['description_en'],
            'description_ar': ad['description_ar'],
            'deed': ad['deed'],
            'bed_type': ad['bed_type'],
            'status': bool(ad['status']),
            'creation_date': ad['creation_date'],
            'update_date': ad['update_date']
        })
    
    return jsonify({'data': data})

@app.route('/admin/api/advertisement/<int:ad_id>/toggle_status', methods=['POST'])
@login_required
def toggle_advertisement_status(ad_id):
    """Toggle advertisement status (active/inactive)"""
    conn = get_db_connection()
    
    # Get current status
    current = conn.execute('SELECT status FROM ilanlar WHERE id = ?', (ad_id,)).fetchone()
    if not current:
        conn.close()
        return jsonify({'success': False, 'message': 'Advertisement not found'}), 404
    
    # Toggle status
    new_status = 0 if current['status'] else 1
    conn.execute('''
        UPDATE ilanlar 
        SET status = ?, update_date = CURRENT_TIMESTAMP 
        WHERE id = ?
    ''', (new_status, ad_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'new_status': bool(new_status)})

@app.route('/admin/advertisement/<int:ad_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_advertisement(ad_id):
    """Edit advertisement"""
    conn = get_db_connection()
    
    if request.method == 'POST':
        # Get current advertisement data
        current_ad = conn.execute('SELECT img_1, img_2, img_3 FROM ilanlar WHERE id = ?', (ad_id,)).fetchone()
        
        # Handle image uploads
        img_1_path = current_ad['img_1']  # Keep existing if no new upload
        img_2_path = current_ad['img_2']
        img_3_path = current_ad['img_3']
        
        # Process image uploads
        if 'img_1' in request.files and request.files['img_1'].filename != '':
            new_path = save_uploaded_file(request.files['img_1'])
            if new_path:
                # Delete old file if it exists and is in upload folder
                if img_1_path and img_1_path.startswith('user_custom_upload/'):
                    try:
                        os.remove(img_1_path)
                    except:
                        pass
                img_1_path = new_path
        
        if 'img_2' in request.files and request.files['img_2'].filename != '':
            new_path = save_uploaded_file(request.files['img_2'])
            if new_path:
                # Delete old file if it exists and is in upload folder
                if img_2_path and img_2_path.startswith('user_custom_upload/'):
                    try:
                        os.remove(img_2_path)
                    except:
                        pass
                img_2_path = new_path
        
        if 'img_3' in request.files and request.files['img_3'].filename != '':
            new_path = save_uploaded_file(request.files['img_3'])
            if new_path:
                # Delete old file if it exists and is in upload folder
                if img_3_path and img_3_path.startswith('user_custom_upload/'):
                    try:
                        os.remove(img_3_path)
                    except:
                        pass
                img_3_path = new_path
        
        # Update advertisement
        conn.execute('''
            UPDATE ilanlar 
            SET title = ?, advertisement_type = ?, adres = ?, is_gold = ?,
                img_1 = ?, img_2 = ?, img_3 = ?, sale_price = ?, rent_price = ?,
                contract_id = ?, description = ?, description_en = ?, description_ar = ?,
                deed = ?, bed_type = ?, update_date = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            request.form['title'],
            request.form['advertisement_type'],
            request.form['adres'],
            1 if 'is_gold' in request.form else 0,
            img_1_path,
            img_2_path,
            img_3_path,
            parse_price(request.form['sale_price']),
            parse_price(request.form['rent_price']),
            request.form['contract_id'],
            request.form['description'],
            request.form['description_en'],
            request.form['description_ar'],
            request.form['deed'],
            request.form['bed_type'],
            ad_id
        ))
        conn.commit()
        conn.close()
        
        flash('Advertisement updated successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    # Get advertisement data for editing
    advertisement = conn.execute('SELECT * FROM ilanlar WHERE id = ?', (ad_id,)).fetchone()
    conn.close()
    
    if not advertisement:
        flash('Advertisement not found!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/edit_advertisement.html', advertisement=advertisement)

@app.route('/admin/advertisement/<int:ad_id>/delete', methods=['POST'])
@login_required
def delete_advertisement(ad_id):
    """Delete advertisement"""
    conn = get_db_connection()
    
    # Get advertisement data to check if it exists and get image paths
    advertisement = conn.execute('SELECT img_1, img_2, img_3 FROM ilanlar WHERE id = ?', (ad_id,)).fetchone()
    
    if not advertisement:
        conn.close()
        flash('Advertisement not found!', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Delete associated image files if they exist in upload folder
    for img_path in [advertisement['img_1'], advertisement['img_2'], advertisement['img_3']]:
        if img_path and img_path.startswith('user_custom_upload/'):
            try:
                os.remove(img_path)
            except:
                pass  # File might not exist, continue anyway
    
    # Delete the advertisement from database
    conn.execute('DELETE FROM ilanlar WHERE id = ?', (ad_id,))
    conn.commit()
    conn.close()
    
    flash('Advertisement deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/advertisement/add', methods=['GET', 'POST'])
@login_required
def add_advertisement():
    """Add new advertisement"""
    if request.method == 'POST':
        conn = get_db_connection()
        
        # Handle image uploads
        img_1_path = None
        img_2_path = None
        img_3_path = None
        
        # Process image uploads
        if 'img_1' in request.files and request.files['img_1'].filename != '':
            img_1_path = save_uploaded_file(request.files['img_1'])
        elif request.form.get('img_1_path'):
            # Use premade image path
            img_1_path = request.form.get('img_1_path')
        
        if 'img_2' in request.files and request.files['img_2'].filename != '':
            img_2_path = save_uploaded_file(request.files['img_2'])
        elif request.form.get('img_2_path'):
            # Use premade image path
            img_2_path = request.form.get('img_2_path')
        
        if 'img_3' in request.files and request.files['img_3'].filename != '':
            img_3_path = save_uploaded_file(request.files['img_3'])
        elif request.form.get('img_3_path'):
            # Use premade image path
            img_3_path = request.form.get('img_3_path')
        
        # Insert new advertisement
        conn.execute('''
            INSERT INTO ilanlar 
            (title, advertisement_type, adres, is_gold, img_1, img_2, img_3, 
             sale_price, rent_price, contract_id, description, description_en, 
             description_ar, deed, bed_type, status, creation_date, update_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (
            request.form['title'],
            request.form['advertisement_type'],
            request.form['adres'],
            1 if 'is_gold' in request.form else 0,
            img_1_path,
            img_2_path,
            img_3_path,
            parse_price(request.form['sale_price']),
            parse_price(request.form['rent_price']),
            request.form['contract_id'],
            request.form['description'],
            request.form['description_en'],
            request.form['description_ar'],
            request.form['deed'],
            request.form['bed_type']
        ))
        conn.commit()
        conn.close()
        
        flash('Advertisement added successfully!', 'success')
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin/add_advertisement.html')

@app.route('/user_custom_upload/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=8025)