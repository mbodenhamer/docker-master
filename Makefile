all: test

VERSION = `cat version.txt | xargs`

PACKAGE = docker-master
IMAGE = mbodenhamer/${PACKAGE}-dev
PYDEV = docker run --rm -it -e BE_UID=`id -u` -e BE_GID=`id -g` \
	-v /var/run/docker.sock:/var/run/docker.sock \
	-v $(CURDIR):/app $(IMAGE)
VERSIONS = 2.7.11,3.4.4,3.5.1

#-------------------------------------------------------------------------------
# Docker image management

docker-build:
	@docker build -t $(IMAGE):latest --build-arg versions=$(VERSIONS) .

docker-first-build:
	@docker build -t $(IMAGE):latest --build-arg versions=$(VERSIONS) \
	--build-arg reqs=requirements.in \
	--build-arg devreqs=dev-requirements.in .
	@$(PYDEV) pip-compile dev-requirements.in
	@$(PYDEV) pip-compile requirements.in

docker-rmi:
	@docker rmi $(IMAGE)

docker-push:
	@docker push ${IMAGE}:latest

docker-pull:
	@docker pull ${IMAGE}:latest

docker-shell:
	@$(PYDEV) bash

.PHONY: docker-build docker-first-build docker-rmi docker-shell
#-------------------------------------------------------------------------------
# Build management

check:
	@$(PYDEV) check-manifest

build: check
	@$(PYDEV) python setup.py sdist bdist_wheel

.PHONY: check build
#-------------------------------------------------------------------------------
# Documentation

docs:
	@$(PYDEV) make -C docs html

view:
	@python -c "import webbrowser as wb; \
	wb.open('docs/_build/html/index.html')"

.PHONY: docs view
#-------------------------------------------------------------------------------
# Dependency management

pip-compile:
	@$(PYDEV) pip-compile dev-requirements.in
	@$(PYDEV) pip-compile requirements.in

.PHONY: pip-compile
#-------------------------------------------------------------------------------
# Tests

test:
	@$(PYDEV) coverage erase
	@$(PYDEV) tox
	@$(PYDEV) coverage html

quick-test:
	@$(PYDEV) bash -c "pip install . && nosetests -v --pdb --pdb-failures"

dist-test: build
	@$(PYDEV) dist-test $(VERSION)

show:
	@python -c "import webbrowser as wb; wb.open('htmlcov/index.html')"

.PHONY: test quick-test dist-test show
#-------------------------------------------------------------------------------
# Cleanup

clean:
	@$(PYDEV) fmap -r ${PACKAGE} 'rm -f' '*.py[co]'
	@$(PYDEV) fmap -r ${PACKAGE} -d rmdir __pycache__
	@$(PYDEV) fmap -r tests 'rm -f' '*.py[co]'
	@$(PYDEV) fmap -r tests -d rmdir __pycache__
	@$(PYDEV) make -C docs clean

.PHONY: clean
#-------------------------------------------------------------------------------
