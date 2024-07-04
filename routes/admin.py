# routes/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from functools import wraps
from models import menus_collection,carts_collection
from werkzeug.utils import secure_filename
import os
from bson import ObjectId

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

UPLOAD_FOLDER = 'static/assets/img/menu'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Unauthorized access')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@admin_required
@login_required
def dashboard():
    return render_template('admin/dashboard.html')

@admin_bp.route('/add_menu', methods=['GET', 'POST'])
@admin_required
@login_required
def add_menu():
    if request.method == 'POST':
        nama_menu = request.form['namaMenu']
        harga_menu = request.form['hargaMenu']
        minimal_pembelian = request.form['minimalPembelian']
        kategori_menu = request.form['kategoriMenu']
        
        # Handle file upload
        if 'gambarMenu' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['gambarMenu']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # Use the product name for the filename, ensuring it's safe and unique
            filename = secure_filename(f"{nama_menu}.{file.filename.rsplit('.', 1)[1].lower()}")
            file_path = os.path.join(UPLOAD_FOLDER, filename).replace("\\", "/")
            file.save(file_path)

            # Save to MongoDB
            menu_item = {
                'nama': nama_menu,
                'harga': int(harga_menu),
                'minimal_pembelian': int(minimal_pembelian),
                'kategori': kategori_menu,
                'gambar': file_path
            }
            menus_collection.insert_one(menu_item)

            flash('Menu Berhasil Di Tambahkan')
            return redirect(url_for('admin.add_menu'))
    menu_count = menus_collection.count_documents({})
    menus = menus_collection.find()
    return render_template('admin/menu.html',menus=menus,menu_count=menu_count)

@admin_bp.route('/delete_menu/<menu_id>', methods=['POST'])
def delete_menu(menu_id):
    menu_item = menus_collection.find_one({'_id': ObjectId(menu_id)})
    if menu_item:
        # Remove the image file from the server
        if 'gambar' in menu_item and os.path.exists(menu_item['gambar']):
            os.remove(menu_item['gambar'])
        
        # Delete the menu item from MongoDB
        menus_collection.delete_one({'_id': ObjectId(menu_id)})
        flash('Menu Telah Terhapus')
        carts_collection.update_many(
            {'cart_items.menu_id': menu_id},
            {'$pull': {'cart_items': {'menu_id': menu_id}}}
        )
    else:
        flash('Menu Tidak Ditemukan')

    return redirect(url_for('admin.add_menu'))

@admin_bp.route('/edit_menu/<menu_id>', methods=['POST'])
def edit_menu(menu_id):
    menus = menus_collection  # Assuming 'menus' is your collection name

    # Ambil data dari form
    nama_menu_baru = request.form.get('editNamaMenu')
    harga_menu = request.form.get('editHargaMenu')
    minimal_pembelian = request.form.get('editMinimalPembelian')
    kategori_menu = request.form.get('editKategoriMenu')
    gambar_menu_baru = request.files.get('editGambarMenu')

    # Validasi data
    if not (nama_menu_baru and harga_menu and minimal_pembelian and kategori_menu):
        flash('Harap lengkapi semua field.', 'danger')
        return redirect(url_for('admin.add_menu'))  # Redirect to your page

    # Ubah tipe data jika diperlukan
    harga_menu = int(harga_menu)
    minimal_pembelian = int(minimal_pembelian)

    # Dapatkan data menu yang akan diubah
    menu_item = menus.find_one({'_id': ObjectId(menu_id)})
    if not menu_item:
        flash('Menu tidak ditemukan.', 'danger')
        return redirect(url_for('admin.add_menu'))

    

    # Persiapkan data yang akan diperbarui
    update_data = {
        'nama': nama_menu_baru,
        'harga': harga_menu,
        'minimal_pembelian': minimal_pembelian,
        'kategori': kategori_menu
    }

    gambar_menu_lama = menu_item.get('gambar', None)

    # Jika ada gambar baru yang diunggah, proses gambar
    if gambar_menu_baru:
        # Secure filename dan simpan di folder uploads atau sesuai kebutuhan
        filename = secure_filename(gambar_menu_baru.filename)
        filename = secure_filename(f"{nama_menu_baru}.{gambar_menu_baru.filename.rsplit('.', 1)[1].lower()}")
        # Simpan gambar di folder static/img atau lokasi yang sesuai
        file_path = os.path.join(UPLOAD_FOLDER, filename).replace("\\", "/")

        # Hapus gambar lama jika ada dan simpan gambar baru
        if gambar_menu_lama and os.path.exists(gambar_menu_lama):
            try:
                os.remove(gambar_menu_lama)
            except OSError as e:
                flash(f'Gagal menghapus gambar lama: {str(e)}', 'danger')

        gambar_menu_baru.save(file_path)
        update_data['gambar'] = file_path
        
    nama_menu_lama = menu_item.get('nama', '')
    # Jika nama menu berubah, ubah juga nama file gambar
    if nama_menu_baru != nama_menu_lama and gambar_menu_lama:
        try:
            # Dapatkan ekstensi gambar lama
            old_ext = gambar_menu_lama.rsplit('.', 1)[1].lower()
            new_filename = secure_filename(f"{nama_menu_baru}.{old_ext}")
            new_file_path = os.path.join(UPLOAD_FOLDER, new_filename).replace("\\", "/")

            # Ubah nama file gambar di server
            os.rename(gambar_menu_lama, new_file_path)
            update_data['gambar'] = new_file_path
        except OSError as e:
            flash(f'Gagal mengubah nama gambar: {str(e)}', 'danger')
        
    # Perbarui dokumen menu di MongoDB
    try:
        menus.update_one(
            {'_id': ObjectId(menu_id)},  # Gunakan ObjectId untuk mencocokkan _id
            {'$set': update_data}
        )
        flash('Menu berhasil diperbarui.', 'success')
    except Exception as e:
        flash(f'Gagal memperbarui menu: {str(e)}', 'danger')

    return redirect(url_for('admin.add_menu'))  # Redirect to your page

