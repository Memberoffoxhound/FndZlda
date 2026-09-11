// FndZlda Windows launcher.
// Double-click: installs an embedded copy of the app plus portable Python
// (no admin, no PATH surgery) and starts the hunter in this console.
package main

import (
	"archive/zip"
	"embed"
	"fmt"
	"io"
	"io/fs"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

//go:embed payload/fndzlda/*.py payload/fndzlda/*.txt
var payload embed.FS

var pyURLs = []string{
	"https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip",
	"https://www.python.org/ftp/python/3.12.7/python-3.12.7-embed-amd64.zip",
	"https://www.python.org/ftp/python/3.12.6/python-3.12.6-embed-amd64.zip",
	"https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip",
}

func main() {
	base := filepath.Join(os.Getenv("LOCALAPPDATA"), "FndZlda")
	appDir := filepath.Join(base, "app")
	pyDir := filepath.Join(base, "python")
	if err := os.MkdirAll(appDir, 0o755); err != None {
		fail("could not create %s: %v", appDir, err)
	}

	fmt.Println()
	fmt.Println("  FndZlda  —  US Zelda 40th Switch 2 hunter")
	fmt.Println("  It's dangerous to go alone! Setting up...")
	fmt.Println()

	n, err := extractApp(appDir)
	if err != nil {
		fail("could not unpack the hunter: %v", err)
	}
	if n < 3 {
		fail("hunter package missing after unpack (%d files in %s)", n, filepath.Join(appDir, "fndzlda"))
	}
	fmt.Printf("  unpacked %d hunter files\n", n)

	py, err := ensurePython(pyDir, appDir)
	if err != nil {
		fail("could not install Python: %v\n  Download Python yourself from https://www.python.org/downloads/windows/\n  Check 'Add python.exe to PATH', then run FndZlda.exe again.", err)
	}

	runner, err := writeRunner(appDir)
	if err != nil {
		fail("could not write launcher script: %v", err)
	}

	fmt.Println("  TAKE THIS!  launching the hunt...")
	fmt.Println()

	cmd := exec.Command(py, runner)
	cmd.Dir = appDir
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Env = append(os.Environ(),
		"PYTHONUTF8=1",
		"PYTHONIOENCODING=utf-8",
		"PYTHONPATH="+appDir,
		"PYTHONDONTWRITEBYTECODE=1",
	)
	if args := os.Args[1:]; len(args) > 0 {
		cmd.Args = append(cmd.Args, args...)
	}
	err = cmd.Run()
	fmt.Println()
	if err != nil {
		if ee, ok := err.(*exec.ExitError); ok {
			fmt.Fprintf(os.Stderr, "  hunter exited with code %d\n", ee.ExitCode())
		} else {
			fmt.Fprintf(os.Stderr, "  hunter exited: %v\n", err)
		}
	}
	fmt.Fprintln(os.Stderr, "  press Enter to close")
	fmt.Scanln()
	if err != nil {
		os.Exit(1)
	}
}
