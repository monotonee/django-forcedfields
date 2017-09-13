.PHONY: build mariadb_cli postgresql_cli tests

build:
	cd src && \
	python setup.py sdist && \
	python setup.py bdist_wheel

mariadb_cli:
	docker-compose exec mariadb mysql

postgres_cli:
	docker-compose exec postgresql psql -U tester

tests:
	python src/runtests.py
	pylint --rcfile=.pylintrc src/django_forcedfields.py

