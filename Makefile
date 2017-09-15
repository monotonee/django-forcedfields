.PHONY: build lint mariadb_cli mysql_cli postgresql_cli tests unit_tests

build:
	cd src && \
	python setup.py sdist && \
	python setup.py bdist_wheel

mariadb_cli:
	docker-compose exec mariadb mysql

mysql_cli:
	docker-compose exec mysql mysql

postgres_cli:
	docker-compose exec postgresql psql -U tester

lint:
	pylint --rcfile=.pylintrc src/django_forcedfields.py

unit_tests:
	python src/runtests.py

tests: unit_tests lint
