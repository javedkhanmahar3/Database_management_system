import streamlit as st
import pandas as pd
from datetime import date
import os

# --- 1. CONFIGURATION & FILE SETUP ---
FILES = {
    "users": "users.csv",       
    "products": "products.csv", 
    "sales": "sales.csv"        
}

# --- 2. INITIALIZATION HELPER FUNCTIONS ---
def init_db():
    if not os.path.exists(FILES["users"]):
        df_users = pd.DataFrame({
            "Username": ["admin"], 
            "Password": ["admin123"], 
            "Role": ["Admin"],
            "Name": ["System Admin"]
        })
        df_users.to_csv(FILES["users"], index=False)
    
    if not os.path.exists(FILES["products"]):
        df_prod = pd.DataFrame([
            {"Name": "Magnum", "Rate": 300},
            {"Name": "Brownie", "Rate": 170},
            {"Name": "Cornetto", "Rate": 130},
            {"Name": "Feast", "Rate": 100},
            {"Name": "Donut", "Rate": 100},
        ])
        df_prod.to_csv(FILES["products"], index=False)

    if not os.path.exists(FILES["sales"]):
        df_sales = pd.DataFrame(columns=[
            "Date", "Hawker", "Product", "Rate", "Load_Out", "Load_In", "Damage", "Sold", "Amount"
        ])
        df_sales.to_csv(FILES["sales"], index=False)

def load_data(key):
    return pd.read_csv(FILES[key])

def save_data(key, df):
    df.to_csv(FILES[key], index=False)

# --- 3. AUTHENTICATION LOGIC ---
def login_user(username, password):
    users = load_data("users")
    user = users[(users["Username"] == username) & (users["Password"] == password)]
    if not user.empty:
        return user.iloc[0]
    return None

# --- 4. ADMIN INTERFACE ---
def admin_interface():
    st.title("👨‍💼 Admin Dashboard - Zuberi Services")
    
    # --- CSS STYLING FOR TABS ---
    # This makes the tabs bigger and bold
    st.markdown("""
    <style>
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 1.2rem;
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)

    # UPDATED TABS: Cleaned names and added the new Report tab
    tabs = st.tabs([
        "📊 Dashboard", 
        "🍦 Products", 
        "👤 Manage Hawkers", 
        "📝 Daily Entry", 
        "📑 Individual Reports" # New Tab
    ])

    # --- TAB 1: DASHBOARD ---
    with tabs[0]:
        st.subheader("Business Overview")
        df_sales = load_data("sales")
        if not df_sales.empty:
            total_rev = df_sales["Amount"].sum()
            total_dmg = df_sales["Damage"].sum()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Revenue", f"Rs. {total_rev}")
            c2.metric("Total Damaged Items", int(total_dmg))
            c3.metric("Total Transactions", len(df_sales))
            
            st.markdown("### Recent Transactions")
            st.dataframe(df_sales.tail(10), use_container_width=True)
            
            csv = df_sales.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Full Report", csv, "report.csv", "text/csv")
        else:
            st.info("No sales data available yet.")

    # --- TAB 2: MANAGE PRODUCTS ---
    with tabs[1]:
        st.subheader("Product Inventory")
        df_prod = load_data("products")
        
        with st.expander("➕ Add New Product"):
            with st.form("add_prod"):
                new_p_name = st.text_input("Product Name")
                new_p_rate = st.number_input("Rate", min_value=1)
                if st.form_submit_button("Add Product"):
                    new_row = pd.DataFrame([{"Name": new_p_name, "Rate": new_p_rate}])
                    df_prod = pd.concat([df_prod, new_row], ignore_index=True)
                    save_data("products", df_prod)
                    st.success(f"Added {new_p_name}")
                    st.rerun()

        edited_df = st.data_editor(df_prod, num_rows="dynamic", key="prod_editor", use_container_width=True)
        if st.button("Save Product Changes"):
            save_data("products", edited_df)
            st.success("Product list updated!")

    # --- TAB 3: MANAGE HAWKERS ---
    with tabs[2]:
        st.subheader("Hawker Management")
        df_users = load_data("users")
        hawkers = df_users[df_users["Role"] == "Hawker"]
        
        with st.expander("➕ Register New Hawker"):
            with st.form("add_hawker"):
                h_name = st.text_input("Full Name")
                h_user = st.text_input("Username (for login)")
                h_pass = st.text_input("Password")
                if st.form_submit_button("Register Hawker"):
                    if h_user in df_users["Username"].values:
                        st.error("Username already exists!")
                    else:
                        new_user = pd.DataFrame([{
                            "Username": h_user, "Password": h_pass, 
                            "Role": "Hawker", "Name": h_name
                        }])
                        df_users = pd.concat([df_users, new_user], ignore_index=True)
                        save_data("users", df_users)
                        st.success(f"Registered {h_name}")
                        st.rerun()

        st.dataframe(hawkers[["Name", "Username", "Role"]], use_container_width=True)

    # --- TAB 4: DAILY ENTRY ---
    with tabs[3]:
        st.write("Admin Override: Enter sales for any hawker.")
        daily_entry_form(is_admin=True)

    # --- TAB 5: INDIVIDUAL REPORTS (NEW!) ---
    with tabs[4]:
        st.subheader("🔎 Individual Hawker Report")
        
        df_sales = load_data("sales")
        df_users = load_data("users")
        
        # Get list of Hawker Names
        hawker_list = df_users[df_users["Role"] == "Hawker"]["Name"].unique()
        
        if len(hawker_list) > 0:
            selected_hawker = st.selectbox("Select a Hawker to view Report:", hawker_list)
            
            # Filter Data
            hawker_data = df_sales[df_sales["Hawker"] == selected_hawker]
            
            if not hawker_data.empty:
                # Calculate Totals for this specific person
                total_h_rev = hawker_data["Amount"].sum()
                total_h_dmg = hawker_data["Damage"].sum()
                total_h_sold = hawker_data["Sold"].sum()
                
                # Display Metrics
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Generated Revenue", f"Rs. {total_h_rev}")
                m2.metric("Total Items Sold", int(total_h_sold))
                m3.metric("Total Damages", int(total_h_dmg))
                
                st.divider()
                st.markdown(f"**Detailed History for {selected_hawker}:**")
                st.dataframe(hawker_data, use_container_width=True)
                
                # Download specific report
                csv_h = hawker_data.to_csv(index=False).encode('utf-8')
                st.download_button(f"📥 Download {selected_hawker}'s Report", csv_h, f"{selected_hawker}_report.csv", "text/csv")
            else:
                st.warning(f"No sales records found for {selected_hawker} yet.")
        else:
            st.info("No Hawkers registered yet.")

# --- 5. HAWKER INTERFACE ---
def hawker_interface(user_info):
    st.title(f"👋 Welcome, {user_info['Name']}")
    
    # Apply same styling to Hawker tabs
    st.markdown("""
    <style>
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 1.2rem;
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📝 Daily Entry", "📜 My History"])
    
    with tab1:
        st.markdown("### Enter Today's Sales")
        daily_entry_form(is_admin=False, default_hawker=user_info["Name"])
        
    with tab2:
        st.markdown("### My Performance")
        df_sales = load_data("sales")
        my_sales = df_sales[df_sales["Hawker"] == user_info["Name"]]
        st.dataframe(my_sales, use_container_width=True)

# --- 6. SHARED COMPONENT: DAILY ENTRY FORM ---
def daily_entry_form(is_admin=False, default_hawker=None):
    df_prod = load_data("products")
    df_users = load_data("users")
    
    if is_admin:
        hawker_list = df_users[df_users["Role"] == "Hawker"]["Name"].tolist()
        if hawker_list:
            hawker_name = st.selectbox("Select Hawker", hawker_list)
        else:
            st.error("No Hawkers found. Please add a Hawker first.")
            return
    else:
        hawker_name = default_hawker

    entry_date = st.date_input("Date", date.today())
    
    with st.form("daily_sales_form"):
        entries = []
        st.markdown(f"**Enter Load Out, Load In, and Damage for {hawker_name}**")
        
        cols = st.columns([3, 1, 2, 2, 2])
        cols[0].write("**Product**")
        cols[1].write("**Rate**")
        cols[2].write("**Load Out**") 
        cols[3].write("**Load In**")  
        cols[4].write("**Damage**")   

        for index, row in df_prod.iterrows():
            c = st.columns([3, 1, 2, 2, 2])
            c[0].write(row["Name"])
            c[1].write(str(row["Rate"]))
            
            l_out = c[2].number_input(f"Out_{row['Name']}", min_value=0, label_visibility="collapsed")
            l_in = c[3].number_input(f"In_{row['Name']}", min_value=0, label_visibility="collapsed")
            dmg = c[4].number_input(f"Dmg_{row['Name']}", min_value=0, label_visibility="collapsed")
            
            if l_out > 0 or l_in > 0 or dmg > 0:
                entries.append({
                    "Date": entry_date,
                    "Hawker": hawker_name,
                    "Product": row["Name"],
                    "Rate": row["Rate"],
                    "Load_Out": l_out,
                    "Load_In": l_in,
                    "Damage": dmg
                })
        
        if st.form_submit_button("Submit Daily Sheet"):
            if entries:
                new_data = []
                for e in entries:
                    sold = e["Load_Out"] - e["Load_In"] - e["Damage"] 
                    amount = sold * e["Rate"]
                    e["Sold"] = sold
                    e["Amount"] = amount
                    new_data.append(e)
                
                df_sales = load_data("sales")
                df_sales = pd.concat([df_sales, pd.DataFrame(new_data)], ignore_index=True)
                save_data("sales", df_sales)
                st.success("Daily sheet saved successfully!")
            else:
                st.warning("No data entered.")

# --- 7. MAIN APP FLOW ---
def main():
    st.set_page_config(page_title="Zuberi Services", layout="wide")
    init_db()
    
    if "user" not in st.session_state:
        st.session_state.user = None

    if st.session_state.user is None:
        st.markdown("<h1 style='text-align: center;'>🍦 Zuberi Services Login</h1>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1,1,1])
        with col2:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.button("Login", use_container_width=True):
                user = login_user(username, password)
                if user is not None:
                    st.session_state.user = user
                    st.rerun()
                else:
                    st.error("Invalid Username or Password")
            
            st.info("Default Admin: user=`admin`, pass=`admin123`")

    else:
        with st.sidebar:
            st.write(f"Logged in as: **{st.session_state.user['Role']}**")
            if st.button("Logout"):
                st.session_state.user = None
                st.rerun()

        if st.session_state.user["Role"] == "Admin":
            admin_interface() 
        else:
            hawker_interface(st.session_state.user) 

if __name__ == "__main__":
    main()
