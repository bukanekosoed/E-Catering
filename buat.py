from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def main():
    # Kata sandi yang ingin di-hash
    password = "admin123"

    # Menghasilkan hash dari password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Mencetak hasil hash
    print("Hash dari password '{}' adalah: {}".format(password, hashed_password))

if __name__ == "__main__":
    main()
