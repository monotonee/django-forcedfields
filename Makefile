.PHONY: build lint mariadb_cli mysql_cli postgresql_cli tests unit_tests tests

build:
	cd src && \
	python setup.py sdist && \
	python setup.py bdist_wheel

mariadb_cli:
	docker-compose exec mariadb mysql

mysql_cli:
	docker-compose exec mysql mysql

postgresql_cli:
	docker-compose exec postgresql psql -U tester

# duplicate-code disabled due to poor implementation in Pylint and unresponsive Pylint config options.
lint:
	pylint --disable=duplicate-code --rcfile=.pylintrc src/django_forcedfields.py src/tests/*.py

unit_tests:
	python src/manage.py test --verbosity 2

tests: unit_tests lint
