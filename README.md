ultimatum_game
==============

Website for the HTI Minor Project on the ultimatum game.

This project requires an installation of Python and Django, as well as some database server. We have tested MySQL along with mysql-python.

Short installation guide:

1. Install the latest version of Python 2.x.
2. Install Django 1.5.x
3. Install MySQL with username root and password root
4. Install mysql-python. This is easiest using pip (sudo pip install mysql-python)
5. Create a database named 'hti'. This can most easily be done by executing: mysql -u root -p -e 'create database hti;'
6. Execute: python manage.py syncdb

The development server can now be started by running: python manage.py runserver
Settings for the connection to the database (which software to use and which credentials to login with) can be set by editing ultimatum_game/settings.py
