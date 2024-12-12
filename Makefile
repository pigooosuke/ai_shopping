# 遷移図の出力
draw_graph:
	docker compose run --rm app python draw_graph.py

ruff:
	docker compose run --rm app ruff check . --fix && \
	docker compose run --rm chroma-init ruff check . --fix