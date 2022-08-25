package main

// program to dig out the job name from worker_log.txt files in the Toil / CWL work dir and make labeled file stubs so we can tell
// which work subdir goes with which workflow task

// https://pkg.go.dev/github.com/vjeantet/grok
// https://github.com/vjeantet/grok
// https://github.com/vjeantet/grok/blob/master/patterns/grok-patterns
// https://github.com/google/re2/wiki/Syntax
// https://grokdebug.herokuapp.com/

import (
	"bufio"
	"fmt"
	"github.com/vjeantet/grok"
	"io/fs"
	"log"
	"os"
	"path/filepath"
	"strings"
)

// log errors to stderr
var logger = log.New(os.Stderr, "", 0)

// find all the files called "worker_log.txt" in the directory tree
func GetWorkerLogs(dirPath string) ([]string, error) {
	// https://pkg.go.dev/io/fs#FileInfo
	// https://pkg.go.dev/io/fs#DirEntry
	// allFiles := []fs.DirEntry{}
	allFiles := []string{}

	// https://pkg.go.dev/path/filepath#WalkDir
	err := filepath.WalkDir(dirPath, func(path string, dirEntry fs.DirEntry, err error) error {
		// skip item that cannot be read
		if os.IsPermission(err) {
			logger.Printf("Skipping path that could not be read %q: %v\n", path, err)
			return filepath.SkipDir
		}
		// return other errors encountered
		if err != nil {
			return err
		}

		if dirEntry.Name() == "worker_log.txt" {
			allFiles = append(allFiles, path)
		}
		return err
	})
	return allFiles, err
}

// read all the lines from a file
func ReadLines(path string) []string {
	file, err := os.Open(path)
	if err != nil {
		logger.Fatalln("Couldn't open the file", err)
	}
	defer file.Close()

	var lines []string

	// need to initialize a buffer for the scanner that is larger than the default 64KB size
	const maxCapacity = 2048 * 1024 // 2Mb
	buf := make([]byte, maxCapacity)
	scanner := bufio.NewScanner(file) // file io.Reader
	scanner.Buffer(buf, maxCapacity)
	for scanner.Scan() {
		var line string
		line = scanner.Text()

		if len(line) > 0 { // && string(line[0]) == string(commentChar)
			lines = append(lines, line)
		} else {
			break
		}

	}
	if err := scanner.Err(); err != nil {
		logger.Fatal(err)
	}

	return lines
}

func MapHasAllKeys(keys []string, m map[string]string) bool {
	var result bool = true
	for _, key := range keys {
		if _, exists := m[key]; !exists {
			result = false
		}
	}
	return result
}

// search for the line that gives the job name
// return results from first line that has the values
func FindJobName(lines []string) (bool, string, string) {
	g, _ := grok.NewWithConfig(&grok.Config{NamedCapturesOnly: true})

	var found bool = false
	for _, line := range lines {
		// [2022-08-23T14:13:06-0400] [MainThread] [I] [foobar] [job some_job_name] /path/to/foo$ command \
		values, err := g.Parse(`^\[%{TIMESTAMP_ISO8601:timestamp}\].*\[job %{WORD:jobname}.*\] %{PATH:path}`, line)
		if err != nil {
			logger.Fatal(err) // fmt.Printf("ERROR: %v\n", err) // return err
		}

		if MapHasAllKeys([]string{"jobname", "path"}, values) {
			found = true
			jobname := values["jobname"]
			path := values["path"]

			// grok pulls in trailing '$' by default, need to remove
			path = strings.Trim(path, "$")

			return found, jobname, path

		}
	}

	return found, "", ""
}

// 'touch' a file to create it
func TouchFile(path string) {
	f, err := os.OpenFile(path, os.O_RDONLY|os.O_CREATE, 0666)
	defer f.Close()
	if err != nil {
		logger.Fatal(err)
	}
}

func main() {
	var startDir string
	args := os.Args[1:]
	if len(args) < 1 {
		logger.Fatal("ERROR: You need to supply a start dir")
	} else {
		startDir = args[0]
	}

	// find all log files
	allFiles, err := GetWorkerLogs(startDir)
	if err != nil {
		logger.Fatal(err)
	}

	for _, path := range allFiles {
		// read all the lines from each file
		allLines := ReadLines(path)

		// search the lines for the jobname
		found, jobname, _ := FindJobName(allLines)

		if found {
			// make path to jobname file ; dirname(path)/jobname
			jobDirPath := filepath.Dir(path) // jobDirPath := filepath.Dir(jobpath) // do not use the path from inside the log in case we moved the log
			jobFilePath := filepath.Join(jobDirPath, jobname)
			// print the path of the file we will create
			fmt.Printf("%v\n", jobFilePath)
			// create a file stub to label the dir contents
			TouchFile(jobFilePath)
		}
	}
}
