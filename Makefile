.PHONY: install test lint fmt run demo deploy docker-build docker-run clean

install:
	python3 -m pip install -e '.[dev]'

test:
	python3 -m pytest -q

lint:
	ruff check src tests scripts

fmt:
	ruff format src tests scripts

run:
	python3 -m guard0.app

demo:
	python3 scripts/demo_april_2026.py

content:
	python3 scripts/generate_content.py --file data/april_2026_incidents.json --severity critical

x-post:
	python3 scripts/x_post.py --file content/hack_guard_thread.json --thread --dry-run

telegram-post:
	python3 scripts/telegram_post.py --file content/hack_guard_thread.json --thread --dry-run

telegram-health:
	python3 scripts/telegram_post.py --health

deploy:
	python3 scripts/deploy_0g.py --network testnet

docker-build:
	docker build -t 0guard:latest .

docker-run:
	docker run -p 8109:8109 --env-file .env 0guard:latest

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	rm -rf .pytest_cache .ruff_cache dist build *.egg-info
