package main

import (
	"github.com/google/go-cmp/cmp"
	"testing"
)

func TestMapHasKeys(t *testing.T) {
	tests := map[string]struct {
		inputKeys []string
		inputMap  map[string]string
		want      bool
	}{
		"first": {
			inputKeys: []string{"a", "b"},
			inputMap:  map[string]string{"a": "foo", "b": "bar", "c": "baz"},
			want:      true,
		},
		"second": {
			inputKeys: []string{"a", "d"},
			inputMap:  map[string]string{"a": "foo", "b": "bar", "c": "baz"},
			want:      false,
		},
	}

	for name, tc := range tests {
		t.Run(name, func(t *testing.T) {
			got := MapHasAllKeys(tc.inputKeys, tc.inputMap)
			if got != tc.want {
				t.Errorf("got %v is not the same as %v", got, tc.want)
			}
		})
	}
}

func TestFindJobName(t *testing.T) {
	type Result struct {
		Found   bool
		Jobname string
		Path    string
	}
	tests := map[string]struct {
		inputLines []string
		want       Result
	}{
		"first": {
			inputLines: []string{
				"a",
				"[2020-07-13T04:10:16-0400] [MainThread] [I] [cwltool] [job maf2vcf] /path/to/foo$ command",
				"b",
			},
			want: Result{
				Found:   true,
				Jobname: "maf2vcf",
				Path:    "/path/to/foo",
			},
		},
		"second": {
			inputLines: []string{
				"a",
				"c",
				"b",
			},
			want: Result{
				Found:   false,
				Jobname: "",
				Path:    "",
			},
		},
	}

	for name, tc := range tests {
		t.Run(name, func(t *testing.T) {
			gotFound, gotJobname, gotPath := FindJobName(tc.inputLines)
			if diff := cmp.Diff(tc.want, Result{gotFound, gotJobname, gotPath}); diff != "" {
				t.Errorf("got vs want mismatch (-want +got):\n%s", diff)
			}
		})
	}
}
