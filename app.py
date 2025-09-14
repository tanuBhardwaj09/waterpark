import streamlit as st
import sqlite3
import qrcode
import io, base64
import pandas as pd
from datetime import datetime, date

# -------------------- CONFIG --------------------
DB_FILE = "booking_db.sqlite"   # single DB file
UPI_ID = "9813589884@ybl"
PRICE_PER_TICKET = 299
ADMIN_PASSWORD = "admin123"  # Change this to a secure password

# -------------------- DB HELPERS --------------------
def get_db_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Create table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone_number TEXT,
            date TEXT,
            tickets INTEGER,
            amount REAL,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

# -------------------- QR CODE DISPLAY --------------------
def make_qr(data):
    qr = qrcode.make(data)
    buf = io.BytesIO()
    qr.save(buf, format="PNG")
    return buf.getvalue()

def show_qr_with_css(img_bytes, title="📱 Scan this QR to Pay"):
    qr_base64 = base64.b64encode(img_bytes).decode("utf-8")
    st.markdown(
        f"""
        <div style="display:flex; justify-content:center; margin-top:20px;">
          <div style="padding:18px; border-radius:16px; background:#f2f8ff;
                      box-shadow:0 10px 30px rgba(2,6,23,0.12); text-align:center;">
            <h4>{title}</h4>
            <img src="data:image/png;base64,{qr_base64}" width="260" />
            <div class="upi-note">UPI ID: <strong>{UPI_ID}</strong></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# -------------------- INIT --------------------
st.set_page_config(page_title="Muskan Waterpark Booking", page_icon="💧", layout="centered")
init_db()

st.title("💧 Muskan Waterpark Booking System 💧")
st.write("Book your tickets and pay via UPI. Booking is saved as `pending` — mark as paid after you confirm payment.")

# -------------------- FORM --------------------
with st.form("booking_form"):
    name = st.text_input("👤 Enter Your Name")
    phone_number = st.text_input("📞 Enter Your Phone Number")
    if phone_number:
        if not (phone_number.isdigit() and len(phone_number) == 10):
            st.warning("⚠️ Please enter a valid 10-digit phone number.")
    visit_date = st.date_input("📅 Date of Visit", min_value=date.today())
    tickets = st.number_input("🎟 Number of Tickets", min_value=1, step=1)
    amount = tickets * PRICE_PER_TICKET

    submitted = st.form_submit_button("Generate UPI QR & Book")

# -------------------- PROCESS BOOKING --------------------
if submitted:
    if not name.strip() or not phone_number.strip():
        st.warning("⚠️ Please enter both name and phone number.")
    else:
        st.info(f"💰 Total Amount: **₹{amount}**")
        upi_link = f"upi://pay?pa={UPI_ID}&pn={name}&am={amount}&cu=INR"
        qr_img = make_qr(upi_link)
        show_qr_with_css(qr_img)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO bookings (name, phone_number, date, tickets, amount, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, phone_number, visit_date.strftime("%Y-%m-%d"), int(tickets), float(amount), "pending")
            )
            conn.commit()
            conn.close()
            st.success(f"📝 Booking saved as pending! Hi **{name}**, please pick up your ticket at the counter after completing the payment using the QR.")
        except Exception as e:
                st.error(f"❌ Error saving booking: {e}")


# -------------------- ADMIN LOGIN --------------------
st.subheader("🔑 Admin Access (to view all bookings)")
admin_password_input = st.text_input("Enter admin password", type="password")

if admin_password_input:
    if admin_password_input == ADMIN_PASSWORD:
        st.success("✅ Access granted")
        try:
            conn = get_db_connection()
            df = pd.read_sql_query("SELECT * FROM bookings ORDER BY created_at DESC", conn)
            conn.close()
            if not df.empty:
                st.dataframe(df)
            else:
                st.info("No bookings yet.")
        except Exception as e:
            st.error(f"❌ Error fetching bookings: {e}")
    else:
        st.error("❌ Wrong password")
