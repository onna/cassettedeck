.PHONEY: develop test clean


develop: venv


test: venv
	./venv/bin/pytest cassettedeck/tests

clean:
	rm -rf venv

venv: setup.py test-requirements.txt
	python3 -m venv --clear venv
	./venv/bin/pip install -U pip wheel setuptools
	./venv/bin/pip install -r test-requirements.txt
	./venv/bin/pip install -e .
