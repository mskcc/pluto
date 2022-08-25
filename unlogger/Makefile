SHELL:=/bin/bash
.ONESHELL:

run:
	go run main.go worker_logs/

format:
	gofmt -l -w main.go
	gofmt -l -w main_test.go

# go test -v ./...
test:
	set -euo pipefail
	go clean -testcache && \
	go test -v . | sed ''/PASS/s//$$(printf "\033[32mPASS\033[0m")/'' | sed ''/FAIL/s//$$(printf "\033[31mFAIL\033[0m")/''


SRC:=main.go
BIN:=unlogger
build:
	go build -o ./$(BIN) ./$(SRC)
.PHONY:build

# fatal: No names found, cannot describe anything.
GIT_TAG:=$(shell git describe --tags)
build-all:
	mkdir -p build ; \
	for os in darwin linux windows; do \
	for arch in amd64 arm64; do \
	output="build/$(BIN)-v$(GIT_TAG)-$$os-$$arch" ; \
	if [ "$${os}" == "windows" ]; then output="$${output}.exe"; fi ; \
	echo "building: $$output" ; \
	GOOS=$$os GOARCH=$$arch go build -o "$${output}" $(SRC) ; \
	done ; \
	done


#
# GOLANG SDK INSTALL METHOD TO USE ON DEV/PROD SERVERS
# ~~~~~ Install Dependencies ~~~~~ #
UNAME:=$(shell uname)
export PATH:=$(CURDIR)/conda/bin:$(PATH)
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
	echo ">>> Setting up conda..." && \
	wget "$(CONDAURL)" && \
	bash "$(CONDASH)" -b -p conda && \
	rm -f "$(CONDASH)"

# activate with;
# source conda/bin/activate
install: conda
	source conda/bin/activate && \
	conda install -y conda-forge::go=1.18.5
