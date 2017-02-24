.PHONY: mariadb_cli postgresql_cli test

mariadb_cli:
	docker run -it --rm --network vagrant_default --link vagrant_mariadb_1 mariadb:latest mysql -hvagrant_mariadb_1 -p3306 -uroot -p

postgres_cli:
	docker run -it --rm --network vagrant_default --link vagrant_postgresql_1 postgres:alpine psql -h vagrant_postgresql_1 -U tester

test:
	python src/runtests.py

