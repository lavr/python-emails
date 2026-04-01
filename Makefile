
clean:
	find . -name '*.pyc'  -exec rm -f {} \;
	find . -name '*.py~'  -exec rm -f {} \;
	find . -name '__pycache__'  -exec rm -rf {} \;
	find . -name '.coverage.*' -exec rm -rf {} \;
	rm -rf build dist emails.egg-info tmp-emails _files

test:
	tox

pypi:
	python setup.py sdist bdist_wheel upload

CODEQL_DB = .codeql-db
CODEQL_PYTHON = .venv/bin/python

codeql-db:
	rm -rf $(CODEQL_DB)
	codeql database create $(CODEQL_DB) --language=python --source-root=. \
		--extractor-option=python.python_executable=$(CODEQL_PYTHON)

codeql-analyze: codeql-db
	codeql pack download codeql/python-queries
	codeql database analyze $(CODEQL_DB) codeql/python-queries \
		--format=sarif-latest --output=codeql-results.sarif

codeql-clean:
	rm -rf $(CODEQL_DB) codeql-results.sarif
