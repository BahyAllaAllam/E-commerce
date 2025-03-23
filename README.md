# E-commerce Platform

![Django](https://img.shields.io/badge/Django-4.2-green.svg)
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.0-purple.svg)

A modern e-commerce platform built with Django, featuring a responsive design and robust shopping cart functionality.

## 🚀 Features

- **User Authentication**
  - Login/Register functionality
  - Password reset capability
  - User profile management

- **Shopping Experience**
  - Dynamic shopping cart
  - Real-time cart updates
  - Product catalog with categories
  - Responsive product search

- **Checkout Process**
  - Secure checkout system
  - Multiple payment options
  - Order tracking
  - Shipping information management

## 🛠️ Technologies Used

- **Backend**
  - Django 4.2
  - Python 3.8+
  - SQLite3 (Development)

- **Frontend**
  - Bootstrap 5
  - JavaScript/jQuery
  - HTML5/CSS3

- **Authentication**
  - Django Allauth
  - Custom user model

## 📦 Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd E-commerce
```

2. Create a virtual environment and activate it:
```bash
python -m venv env
source env/bin/activate  # On Windows use: env\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
- Create a `.env` file in the project root
- Add required environment variables:
  ```
  SECRET_KEY=your_secret_key
  DEBUG=True
  EMAIL_USER=your_email
  EMAIL_PASSWORD=your_email_password
  ```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

## 🌐 Usage

1. Access the admin panel at `http://localhost:8000/admin`
2. Add products through the admin interface
3. Visit `http://localhost:8000` to view the store
4. Register a new account or login
5. Start shopping!

## 🔒 Security Features

- CSRF protection
- Secure password hashing
- Protected user data
- Secure checkout process

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- Your Name - Initial work

## 🙏 Acknowledgments

- Django documentation
- Bootstrap team
- All contributors

---
⭐️ Star this repository if you find it helpful!
