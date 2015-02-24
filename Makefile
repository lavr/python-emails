
clean:
	find . -name '*pyc'  -exec rm -f {} \;
	find . -name '*py~'  -exec rm -f {} \;

test:
	tox

pypi:
	python setup.py sdist bdist_wheel upload
