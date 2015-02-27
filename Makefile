
clean:
	find . -name '*.pyc'  -exec rm -f {} \;
	find . -name '*.py~'  -exec rm -f {} \;
	rm -rf build dist emails.egg-info tmp-emails _files

test:
	tox

pypi:
	python setup.py sdist bdist_wheel upload
