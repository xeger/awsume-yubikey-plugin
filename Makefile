.PHONY: build clean preview publish

build:
	python3 setup.py bdist_wheel

clean:
	rm -Rf build dist *.egg-info

preview:
	pip3 install .

uninstall:
	pip3 uninstall awsume-yubikey-plugin

publish:
	twine upload dist/*
