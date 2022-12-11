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

test:
	pytest -n 4 --ignore docs -s .
	CWL_ENGINE=toil pytest -n 4 --ignore docs -s .


lint:
	mypy --namespace-packages --explicit-package-bases .