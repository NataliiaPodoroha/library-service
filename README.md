# Library Management API Service

RESTful API for online management system for tracking books, borrowings, users & payments in the library. The API allows users to create profiles, to borrow books and create borrowing record, make payments for book borrowings through the Stripe platform and return books.

## Features

**Books Inventory Management**:

* The system allows CRUD operations for books and manages books inventory

**Users Management**:

* Creating users and updating users information
* JWT authentication for users
* Only authenticated users have access to the features of the system
* Admin users have additional privileges to manage information within the system

**Borrowing Management**:

* Users can borrow and return books, the inventory of books will be updated accordingly
* Filtering by active borrowings (still not returned) is available for all authenticated users
* Filtering by user id parameter is available for admin users (so admin can see borrowings of a concrete user)


**Payments Management**:

* The system supports payments for book borrowings through the Stripe platform.

**Swagger Documentation**

**Docker Containerization**

* The application is containerized using Docker for simplified deployment and management.


## Technologies

[Django](https://docs.djangoproject.com/en/4.2/) - A high-level Python web framework that encourages rapid development and clean, pragmatic design.

[Django Rest Framework (DRF)](https://www.django-rest-framework.org/) - A powerful and flexible toolkit for building Web APIs.

[PostgreSQL](https://www.postgresql.org/docs/) - A powerful, open-source object-relational database system.

[Stripe](https://stripe.com/docs) - A platform for processing online payments, commonly used in Django Rest Framework projects to manage financial transactions in web applications.

[Docker](https://docs.docker.com/) - A platform for developing, shipping, and running applications using containerization.

[Swagger](https://swagger.io/docs/) - An open-source software framework backed by a large ecosystem of tools that helps developers design, build, document, and consume RESTful web services.

[JWT](https://jwt.io/introduction/) - JSON Web Tokens are used for securely transmitting information between parties as a JSON object.


## How to launch locally:

1. Clone the repository:

   ```
   git clone https://github.com/PodorogaNatalia/library-service
   ```

2. Navigate to the project directory:

   ```
   cd library-service
   ```

3. Create and activate a virtual environment:

   ```
   python -m venv venv
   
   source venv/bin/activate # For Mac OS/Linux
   
   venv\Scripts\activate  # For Windows
   ```

4. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```

5. Create .env file and define environmental variables following .env.sample


6. Install PostgreSQL and create a data base


7. Run the database migrations:

   ```
   python manage.py migrate
   ```

8. Run the development server:

   ```
   python manage.py runserver
   ```
   

## How to launch with docker:

1. Clone the repository:

   ```
   git clone https://github.com/PodorogaNatalia/library-service
   ```
   
2. Create .env file and define environmental variables following .env.sample


3. Install Docker on your machine.

   
4. Run command:

   ```
   docker-compose up --build
   ```
   
5. You should use such localhost for you app: ```127.0.0.1:8000```


## Service has next endpoints:
   ```
   "book" : 
                "http://127.0.0.1:8000/api/book/"
                "http://127.0.0.1:8000/api/book/{id}/"
   "borrowing" : 
                "http://127.0.0.1:8000/api/borrowing/"
                "http://127.0.0.1:8000/api/borrowing/{id}/"
                "http://127.0.0.1:8000/api/borrowing/{id}/return/"
   "payment" : 
                "http://127.0.0.1:8000/api/payment/"
                "http://127.0.0.1:8000/api/payment/{id}/"
                "http://127.0.0.1:8000/api/payment/{id}/cancelled/"
                "http://127.0.0.1:8000/api/payment/{id}/success/"
   "user" : 
                   "http://127.0.0.1:8000/api/user/"
                   "http://127.0.0.1:8000/api/user/{id}/"
                   "http://127.0.0.1:8000/api/user/token/"
                   "http://127.0.0.1:8000/api/user/token/refresh/"
                   "http://127.0.0.1:8000/api/user/token/verify/"
   "documentation": 
                   "http://127.0.0.1:8000/api/swagger/"
                   "http://127.0.0.1:8000/api/redoc/"
   ```

## How to access

Create superuser:

   ```
   python manage.py createsuperuser
   ```

Also, you can create ordinary user at such endpoint:

   ```
   "http://127.0.0.1:8000/api/user/"
   ```

To work with token use such endpoints:

   ```
   "http://127.0.0.1:8000/api/user/token/" - to get access and refresh token
   "http://127.0.0.1:8000/api/user/token/refresh/" - to refresh access token
   "http://127.0.0.1:8000/api/user/token/verify/" - to verify access token
   ```

Add Token in api urls in Headers as follows:

   ```
   key: Authorize
   value: Bearer @token
   ```
