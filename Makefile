.PHONY: run restart check

run:
	./run.sh

restart:
	./restart.sh

check:
	python3 -m py_compile app/server.py
