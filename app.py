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