import streamlit as st
import sqlite3
import os
from PIL import Image
import io
import streamlit_authenticator as stauth

# Set up the SQLite database
def init_db():
    conn = sqlite3.connect("diseases_db.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS disease_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        disease_name TEXT NOT NULL,
        file_name TEXT NOT NULL,
        image BLOB NOT NULL,
        upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    return conn

# Save image to the database
def save_image_to_db(conn, disease_name, image_file, file_name):
    cursor = conn.cursor()
    image_binary = image_file.read()
    cursor.execute("""
    INSERT INTO disease_images (disease_name, file_name, image)
    VALUES (?, ?, ?)
    """, (disease_name, file_name, image_binary))
    conn.commit()

# Fetch all images from the database
def fetch_images_from_db(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM disease_images")
    return cursor.fetchall()

# Fetch single image by ID
def fetch_image_by_id(conn, image_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM disease_images WHERE id=?", (image_id,))
    return cursor.fetchone()

# Update image metadata (disease name)
def update_image_metadata(conn, image_id, new_disease_name):
    cursor = conn.cursor()
    cursor.execute("UPDATE disease_images SET disease_name=? WHERE id=?", (new_disease_name, image_id))
    conn.commit()

# Delete image from the database
def delete_image_from_db(conn, image_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM disease_images WHERE id=?", (image_id,))
    conn.commit()

# Authentication Setup
def authenticate():
    # Define users (username, password, name)
    users = {
        "user1": {"password": "password123", "name": "John Doe"},
        "user2": {"password": "password456", "name": "Jane Smith"},
    }
    # Create a list of usernames and passwords
    usernames = list(users.keys())
    passwords = [users[username]["password"] for username in usernames]
    
    # Use Streamlit-Authenticator to authenticate
    authenticator = stauth.Authenticate(
        usernames,
        passwords,
        cookie_name="disease_image_app",
        key="some_unique_key",  # Replace with a unique string
        cookie_expiry_days=30,
    )
    
    name, authentication_status = authenticator.login("Login", "main")

    return name, authentication_status

# Streamlit UI
def upload_image():
    st.title("Disease Image Upload Portal")
    st.write("Only authenticated users can upload and manage images.")

    # Input for disease name
    disease_name = st.text_input("Enter Disease Name:")
    
    # File upload
    uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "png", "jpeg", "bmp", "tiff"])

    if uploaded_file is not None:
        # Read the image
        image = Image.open(uploaded_file)
        
        # Show the image in Streamlit
        st.image(image, caption=f"Uploaded Image for {disease_name}", use_column_width=True)
        
        # Button to save image to the database
        if st.button("Upload Image to Database"):
            conn = init_db()
            save_image_to_db(conn, disease_name, uploaded_file, uploaded_file.name)
            st.success("Image successfully uploaded!")

# Display all uploaded images with CRUD functionality
def display_uploaded_images():
    st.subheader("Uploaded Images")
    conn = init_db()
    images = fetch_images_from_db(conn)

    if images:
        for image_data in images:
            image_id, disease_name, file_name, image_binary, upload_time = image_data
            image = Image.open(io.BytesIO(image_binary))
            
            st.image(image, caption=f"Disease: {disease_name}, File: {file_name}", use_column_width=True)
            st.write(f"Uploaded at: {upload_time}")
            
            # CRUD options: Update or Delete
            with st.expander(f"Options for {file_name}"):
                new_disease_name = st.text_input(f"Update disease name for {file_name}", disease_name)
                
                # Update button
                if st.button(f"Update {file_name}"):
                    update_image_metadata(conn, image_id, new_disease_name)
                    st.success(f"Image {file_name} metadata updated!")

                # Delete button
                if st.button(f"Delete {file_name}"):
                    delete_image_from_db(conn, image_id)
                    st.success(f"Image {file_name} deleted from database.")
                    st.experimental_rerun()  # Refresh the page after deletion
    else:
        st.write("No images uploaded yet.")

# Main function to control the flow of the app
def main():
    name, authentication_status = authenticate()

    if authentication_status:
        st.write(f"Welcome {name}!")

        menu = ["Upload Image", "View Uploaded Images"]
        choice = st.sidebar.selectbox("Select an option", menu)

        if choice == "Upload Image":
            upload_image()
        elif choice == "View Uploaded Images":
            display_uploaded_images()

    elif authentication_status is False:
        st.error("Authentication failed. Please check your credentials.")

    else:
        st.warning("Please log in to continue.")

if __name__ == "__main__":
    main()
