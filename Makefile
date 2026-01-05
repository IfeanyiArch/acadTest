local-makemigrations:
	docker compose -f local.yaml  run --rm acad python manage.py makemigrations

local-migrate:
	docker compose -f local.yaml run --rm acad python manage.py migrate && make local-down

local-reset:
	docker compose -f local.yaml run --rm acad python manage.py reset_db	

local-run:
	docker compose -f local.yaml up --no-build --abort-on-container-exit

local-down:
	docker compose -f local.yaml down

local-down-v:
	docker compose -f local.yaml down -v --remove-orphans

local-run-build:
	make local-down && docker compose -f local.yaml up --build 

local-seed:
	docker compose -f local.yaml run --rm acad python manage.py seed_database

local-createsuperuser:
	docker compose -f local.yaml run  --rm acad python manage.py createsuperuser

test:
	docker-compose -f test.yaml --env-file .env.test build && docker-compose -f test.yaml --env-file .env.test up --abort-on-container-exit

test-clean:	
	docker compose -f test.yaml down -v --remove-orphans
