SHELL:=/bin/bash
.ONESHELL:
UNAME:=$(shell uname)

export PATH:=$(CURDIR)/conda/bin:$(CURDIR)/bin:$(PATH)
unexport PYTHONPATH
unexport PYTHONHOME

ifeq ($(UNAME), Darwin)
CONDASH:=Miniconda3-4.7.12-MacOSX-x86_64.sh
endif

ifeq ($(UNAME), Linux)
CONDASH:=Miniconda3-4.7.12-Linux-x86_64.sh
endif

CONDAURL:=https://repo.anaconda.com/miniconda/$(CONDASH)

conda:
	@set +e
	echo ">>> Setting up conda..."
	wget "$(CONDAURL)"
	bash "$(CONDASH)" -b -p conda
	rm -f "$(CONDASH)"

# install for self-contained conda in current dir
install: conda
	. conda/bin/activate && \
	conda env update --file environment.yml
# source conda/bin/activate
# conda deactivate

# install into pre-existing conda
# conda env create -n pluto -f environment.yml
# conda activate pluto


# $ python3 -m unittest test_tables.py
# python3 -m unittest discover .
# CWL_ENGINE=toil python3 -m unittest discover .
test:
	pytest --ignore docs -n auto .
	CWL_ENGINE=toil pytest --ignore docs -n auto .


lint:
	mypy --namespace-packages --explicit-package-bases .