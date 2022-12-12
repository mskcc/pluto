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

# source conda/bin/activate
# conda deactivate
install: conda
	. conda/bin/activate && \
	conda env update --file environment.yml


# $ python3 -m unittest test_tables.py
# python3 -m unittest discover .
# CWL_ENGINE=toil python3 -m unittest discover .
test:
	pytest --ignore docs -n auto .
	CWL_ENGINE=toil pytest --ignore docs -n auto .

# https://pytest-xdist.readthedocs.io/en/latest/distribution.html
# https://docs.pytest.org/en/7.2.x/how-to/unittest.html#unittest