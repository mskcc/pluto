# unlogger

Program to dig out the CWL job names from Toil `worker_log.txt` files and write them back into their directories as file stubs.

So that you can browse the Toil CWL work dir for debugging and determine more easily which temp files are associated with which CWL workflow tasks.

# Usage

```
$ ./unlogger path/to/workDir
```

# Install

## Compile from Source

### Install Go

If you do not already have Go 1.18+ installed, you can install it locally via `conda` with:

```
make install
```

Activate it with

```
source conda/bin/activate
```

Check with

```
$ which go
/.../unlogger/conda/bin/go

$ go version
go version go1.18.5 linux/amd64
```

### Compile

Compile the source code with

```
make build
```

The output will be the executable `unlogger` file.
