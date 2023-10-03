.PHONY: build clean preview publish

build:
	python3 setup.py bdist_wheel

clean:
	rm -Rf build dist *.egg-info

preview:
	pip3 install .

publish:
	twine upload dist/*
