from flask import Flask, request, redirect, url_for, render_template, jsonify, session
import mysql.connector
from models import User
import hashlib

application = Flask(__name__)
application.config["SECRET_KEY"] = "1234567890987654321"
application.config["DB_USER"] = "root"
application.config["DB_PASSWORD"] = "root"
application.config["DB_NAME"] = "oabong"
application.config["DB_HOST"] = "localhost"

conn = cursor = None


def openDb():
    global conn, cursor
    conn = mysql.connector.connect(
        user=application.config["DB_USER"],
        password=application.config["DB_PASSWORD"],
        database=application.config["DB_NAME"],
        host=application.config["DB_HOST"],
    )
    cursor = conn.cursor()


def closeDb():
    global conn, cursor
    cursor.close()
    conn.close()


@application.route("/")
def index():
    if "username" in session:
        username = session["username"]
        return render_template("dashboard.html", username=username)
    return redirect(url_for("login"))


# -------------------------------------------------------------------------*/LOGIN FUNCTION/*-------------------------------------------------------------------------------


@application.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = User(username, password)
        if user.authenticate():
            session["username"] = username
            return redirect(url_for("dashboard"))
        pesan = "gagal"
        return render_template("login.html", pesan=pesan)
    pesan = "belum_login"
    return render_template("login.html", pesan=pesan)


@application.route("/logout")
def logout():
    session.pop("username", None)
    session.clear()
    pesan = "logout"
    return render_template("login.html", pesan=pesan)


# -------------------------------------------------------------------------*/MODUL TRANSAKSI/*----------------------------------------------------------------------------


@application.route("/transaksi")
def transaksi():
    openDb()
    cursor.execute("SELECT * FROM transaksi")
    container = []
    for (
        id,
        nama,
        tanggal,
        kategori,
        jumlah_pesanan,
        harga_total,
    ) in cursor.fetchall():
        container.append((id, nama, tanggal, kategori, jumlah_pesanan, harga_total))
    closeDb()
    return render_template("transaksi.html", container=container)


from datetime import datetime


@application.route("/tambahtransaksi", methods=["GET", "POST"])
def tambahtransaksi():
    openDb()
    cursor.execute("SELECT nama FROM pelanggan")
    pelanggan = cursor.fetchall()
    closeDb()

    if request.method == "POST":
        nama = request.form["nama"]
        tanggal = request.form["tanggal"]
        kategori = request.form["kategori"]
        jumlah_pesanan = request.form["jumlah_pesanan"]
        harga_total = request.form["harga_total"]
        data = (nama, tanggal, kategori, jumlah_pesanan, harga_total)

        openDb()
        cursor.execute(
            """
            INSERT INTO transaksi (nama, tanggal, kategori, jumlah_pesanan, harga_total)
            VALUES(%s, %s, %s, %s, %s)
            """,
            data,
        )
        transaksi_id = cursor.lastrowid
        conn.commit()
        closeDb()

        return redirect(url_for("transaksi", transaksi_id=transaksi_id))
    else:
        return render_template("tambahtransaksi.html", pelanggan=pelanggan)


harga_tiket = {"reguler": 15000, "nanggung": 25000, "sepuasnya": 35000}


@application.route("/transaksi_ubah/<id>", methods=["GET", "POST"])
def transaksi_ubah(id):
    openDb()
    cursor.execute("SELECT * FROM transaksi WHERE id='%s'" % id)
    data = cursor.fetchone()

    cursor.execute("SELECT nama FROM pelanggan")
    pelanggan = cursor.fetchall()

    if request.method == "POST":
        id = request.form["id"]
        nama = request.form["nama"]
        tanggal = request.form["tanggal"]
        kategori = request.form["kategori"]
        jumlah_pesanan = request.form["jumlah_pesanan"]

        # Hitung harga total berdasarkan kategori tiket
        harga_total = int(jumlah_pesanan) * harga_tiket[kategori]

        cursor.execute(
            """
            UPDATE transaksi SET nama='%s', tanggal='%s', kategori='%s', jumlah_pesanan='%s', harga_total='%s'
            WHERE id='%s'
        """
            % (nama, tanggal, kategori, jumlah_pesanan, harga_total, id)
        )
        conn.commit()
        closeDb()
        return redirect(url_for("transaksi"))
    else:
        closeDb()
        return render_template("ubahtransaksi.html", data=data, pelanggan=pelanggan)


@application.route("/transaksi_hapus/<id>", methods=["GET", "POST"])
def transaksi_hapus(id):
    openDb()
    cursor.execute("DELETE FROM transaksi WHERE id='%s'" % id)
    conn.commit()
    closeDb()
    return redirect(url_for("transaksi"))


# -----------------------------------------------------------------------*/MODUL PELANGGAN/*------------------------------------------------------------------------------


@application.route("/pelanggan")
def pelanggan():
    openDb()
    cursor.execute("SELECT id, nama, nomor_telepon, alamat FROM pelanggan")
    container = []
    for (
        id,
        nama,
        nomor_telepon,
        alamat,
    ) in cursor.fetchall():
        container.append((id, nama, nomor_telepon, alamat))
    closeDb()
    return render_template("pelanggan.html", container=container)


@application.route("/tambahpelanggan", methods=["GET", "POST"])
def tambahpelanggan():
    if request.method == "POST":
        nama = request.form["nama"]
        nomor_telepon = request.form["nomor_telepon"]
        alamat = request.form["alamat"]
        data = [(nama, nomor_telepon, alamat)]
        openDb()
        cursor.executemany(
            """
        INSERT INTO pelanggan (nama, nomor_telepon, alamat)
        VALUES (%s, %s, %s)
        """,
            data,
        )
        conn.commit()
        closeDb()
        return redirect(url_for("pelanggan"))
    else:
        return render_template("tambahpelanggan.html")


@application.route("/pelanggan_ubah/<id>", methods=["GET", "POST"])
def pelanggan_ubah(id):
    openDb()
    cursor.execute("SELECT * FROM pelanggan WHERE id='%s'" % id)
    data = cursor.fetchone()
    if request.method == "POST":
        id = request.form["id"]
        nama = request.form["nama"]
        nomor_telepon = request.form["nomor_telepon"]
        alamat = request.form["alamat"]

        cursor.execute(
            """
            UPDATE pelanggan SET nama='%s', nomor_telepon='%s', alamat='%s'
            WHERE id='%s'
        """
            % (nama, nomor_telepon, alamat, id)
        )
        conn.commit()
        closeDb()
        return redirect(url_for("pelanggan"))
    else:
        closeDb()
        return render_template("ubahpelanggan.html", data=data)


@application.route("/pelanggan_hapus/<id>", methods=["GET", "POST"])
def pelanggan_hapus(id):
    openDb()
    cursor.execute("DELETE FROM pelanggan WHERE id='%s'" % id)
    conn.commit()
    closeDb()
    return redirect(url_for("pelanggan"))


# ------------------------------------------------------------------------*/MODUL PENGGUNA/*------------------------------------------------------------------------------


@application.route("/pengguna")
def admin():
    openDb()
    cursor.execute("SELECT * FROM admin")
    container = []
    for (
        id,
        nama,
        username,
        password,
    ) in cursor.fetchall():
        container.append((id, nama, username, password))
    closeDb()
    return render_template("pengguna.html", container=container)


@application.route("/tambahpengguna", methods=["GET", "POST"])
def tambahpengguna():
    if request.method == "POST":
        nama = request.form["nama"]
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = hashlib.md5(password.encode()).hexdigest()
        data = [(nama, username, hashed_password)]  # Mengubah data menjadi list
        openDb()
        cursor.executemany(
            """
        INSERT INTO admin (id, nama, username, password)
        VALUES (NULL, %s, %s, %s)
        """,
            data,
        )
        conn.commit()
        closeDb()
        return redirect(url_for("admin"))
    else:
        return render_template("tambahpengguna.html")


@application.route("/ubah/<id>", methods=["GET", "POST"])
def ubah(id):
    openDb()
    cursor.execute("SELECT * FROM admin WHERE id='%s'" % id)
    data = cursor.fetchone()
    if request.method == "POST":
        id = request.form["id"]
        nama = request.form["nama"]
        username = request.form["username"]
        password = request.form["password"]

        # Mengenkripsi password baru dengan algoritma MD5
        hashed_password = hashlib.md5(password.encode()).hexdigest()

        cursor.execute(
            """
            UPDATE admin SET nama='%s', username='%s', password='%s'
            WHERE id='%s'
            """
            % (nama, username, hashed_password, id)
        )
        conn.commit()
        closeDb()
        return redirect(url_for("admin"))
    else:
        closeDb()
        return render_template("ubahpengguna.html", data=data)


@application.route("/hapus/<id>", methods=["GET", "POST"])
def hapus(id):
    openDb()
    cursor.execute("DELETE FROM admin WHERE id='%s'" % id)
    conn.commit()
    closeDb()
    return redirect(url_for("admin"))


# ----------------------------------------------------------------------------*/INVOICE/*---------------------------------------------------------------------------------


@application.route("/invoice/<int:transaksi_id>")
def invoice(transaksi_id):
    openDb()
    cursor.execute("SELECT * FROM transaksi WHERE id = %s", (transaksi_id,))
    transaksi = cursor.fetchone()
    closeDb()

    if transaksi:
        nama = transaksi[1]
        tanggal = transaksi[2]
        kategori = transaksi[3]
        jumlah_pesanan = transaksi[4]
        harga_total = transaksi[5]

        # Mendapatkan harga tiket berdasarkan kategori
        if kategori == "reguler":
            harga_satuan = 15000
        elif kategori == "nanggung":
            harga_satuan = 25000
        elif kategori == "sepuasnya":
            harga_satuan = 35000
        else:
            return "Kategori tiket tidak valid"

        # Menghitung subtotal dan total
        subtotal = jumlah_pesanan * harga_satuan
        total = harga_total

        return render_template(
            "invoice.html",
            nama=nama,
            tanggal=tanggal,
            kategori=kategori,
            jumlah_pesanan=jumlah_pesanan,
            harga_satuan=harga_satuan,
            subtotal=subtotal,
            total=total,
        )
    else:
        return "Transaksi tidak ditemukan"


@application.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# ----------------------------------------------------------------------------*/LAPORAN/*----------------------------------------------------------------------------------


@application.route("/laporan")
def laporan():
    openDb()
    cursor.execute(
        "SELECT kategori, SUM(jumlah_pesanan) as total_pesanan, SUM(harga_total) as total_pendapatan FROM transaksi GROUP BY kategori"
    )
    data = cursor.fetchall()

    total_pendapatan = 0
    for row in data:
        total_pendapatan += row[2]

    closeDb()
    return render_template("laporan.html", data=data, total_pendapatan=total_pendapatan)


@application.route("/get_transaksi_data")
def get_transaksi_data():
    openDb()
    cursor.execute(
        "SELECT kategori, COUNT(*) AS jumlah FROM transaksi GROUP BY kategori"
    )
    result = cursor.fetchall()
    closeDb()

    data = [{"kategori": row[0], "jumlah": row[1]} for row in result]
    return jsonify(data)


if __name__ == "__main__":
    application.run(debug=True)


# ----------------NOTES--------------------------
# @application.route("/laporan")
# def laporan():
#     openDb()
#     cursor.execute("SELECT * FROM transaksi")
#     transaksi_list = cursor.fetchall()
#     closeDb()

#     return render_template("laporan.html", transaksi_list=transaksi_list)


# @application.route("/get_laporan_pendapatan")
# def get_laporan_pendapatan():
#     openDb()
#     cursor.execute(
#         "SELECT kategori, SUM(harga_total) AS total_pendapatan FROM transaksi GROUP BY kategori"
#     )
#     result = cursor.fetchall()

#     # Menghitung total pendapatan dari ketiga kategori tiket
#     total_pendapatan = sum(row[1] for row in result)

#     closeDb()

#     data = [{"kategori": row[0], "total_pendapatan": row[1]} for row in result]

#     # Menambahkan total pendapatan dari ketiga kategori tiket ke dalam data
#     data.append({"kategori": "Total Pendapatan", "total_pendapatan": total_pendapatan})

#     return jsonify(data)


# @application.route("/")
# def main():
#     return render_template("index.html")
