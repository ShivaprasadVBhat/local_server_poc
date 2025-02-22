# change_password.py
from werkzeug.security import generate_password_hash
import getpass
import os

def change_credentials():
    print("\n=== Change File Storage API Credentials ===\n")
    
    # Get new credentials
    username = input("Enter new username (leave blank to keep current): ").strip()
    password = getpass.getpass("Enter new password (leave blank to keep current): ").strip()
    
    if not username and not password:
        print("No changes requested. Exiting.")
        return
    
    # Read current credentials
    current_username = None
    current_password = None
    try:
        with open('credentials.txt', 'r') as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("Username:"):
                    current_username = line.split("Username:")[1].strip()
                elif line.startswith("Password:"):
                    current_password = line.split("Password:")[1].strip()
    except FileNotFoundError:
        print("No credentials file found. Creating a new one.")
    
    # Use current values if no new ones provided
    if not username:
        username = current_username or "admin"
        print(f"Using existing username: {username}")
    
    if not password:
        if current_password:
            print("Using existing password (hidden)")
            password = current_password
        else:
            print("No existing password found. You must set a new password.")
            password = getpass.getpass("Enter new password: ").strip()
            if not password:
                print("Password cannot be empty. Exiting.")
                return
    
    # Generate password hash
    password_hash = generate_password_hash(password)
    
    # Update main app.py file with the new credentials
    try:
        with open('app.py', 'r') as f:
            content = f.read()
        
        # Find the users dictionary in the app.py file
        user_start = content.find("users = {")
        if user_start != -1:
            user_end = content.find("}", user_start)
            if user_end != -1:
                # Replace the users dictionary with the new credentials
                new_users_dict = f'users = {{\n    "{username}": generate_password_hash("{password}")\n}}'
                new_content = content[:user_start] + new_users_dict + content[user_end+1:]
                
                # Write the updated content back to app.py
                with open('app.py', 'w') as f:
                    f.write(new_content)
                print("Updated app.py with new credentials.")
            else:
                print("Could not find the end of users dictionary in app.py.")
                return
        else:
            print("Could not find users dictionary in app.py.")
            return
    except Exception as e:
        print(f"Error updating app.py: {e}")
        return
    
    # Create or update the credentials.txt file
    try:
        with open('credentials.txt', 'w') as f:
            f.write(f"Username: {username}\n")
            f.write(f"Password: {password}\n")
        print("Updated credentials.txt with new credentials.")
    except Exception as e:
        print(f"Error updating credentials.txt: {e}")
    
    print("\nCredentials updated successfully!")
    print(f"New username: {username}")
    print("New password: (hidden for security)")
    print("\nRestart the server for changes to take effect.")

if __name__ == "__main__":
    change_credentials()