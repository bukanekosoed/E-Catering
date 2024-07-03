import bcrypt

def hash_password(password):
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

# Contoh penggunaan fungsi hash_password
plaintext_password = "admin123"
hashed_password = hash_password(plaintext_password)
print("Password hash:", hashed_password)
