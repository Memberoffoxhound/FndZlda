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

//go:embed payload/fndzlda/*.py
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
	if err := os.MkdirAll(appDir, 0o755); err != nil {
		fail("could not create %s: %v", appDir, err)
	}

	fmt.Println()
	fmt.Println("  FndZlda  —  US Zelda 40th Switch 2 hunter")
	fmt.Println("  It's dangerous to go alone! Setting up...")
	fmt.Println()

	if err := extractApp(appDir); err != nil {
		fail("could not unpack the hunter: %v", err)
	}
	py, err := ensurePython(pyDir)
	if err != nil {
		fail("could not install Python: %v\n  Download Python yourself from https://www.python.org/downloads/windows/\n  Check 'Add python.exe to PATH', then run FndZlda.exe again.", err)
	}

	fmt.Println("  TAKE THIS!  launching the hunt...")
	fmt.Println()

	cmd := exec.Command(py, "-m", "fndzlda")
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
	if err := cmd.Run(); err != nil {
		if ee, ok := err.(*exec.ExitError); ok {
			os.Exit(ee.ExitCode())
		}
		fail("hunter exited: %v", err)
	}
}

func extractApp(appDir string) error {
	pkg := filepath.Join(appDir, "fndzlda")
	if err := os.MkdirAll(pkg, 0o755); err != nil {
		return err
	}
	return fs.WalkDir(payload, "payload/fndzlda", func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() {
			return nil
		}
		b, err := payload.ReadFile(path)
		if err != nil {
			return err
		}
		name := filepath.Base(path)
		return os.WriteFile(filepath.Join(pkg, name), b, 0o644)
	})
}

func ensurePython(pyDir string) (string, error) {
	exe := filepath.Join(pyDir, "python.exe")
	if pythonWorks(exe) {
		_ = enableSite(pyDir)
		fmt.Println("  Python already on disk.")
		return exe, nil
	}

	if sysPy := systemPython(); sysPy != "" {
		fmt.Println("  Using Python already on this PC.")
		return sysPy, nil
	}

	fmt.Println("  No Python yet. Downloading a portable copy (python.org)...")
	_ = os.RemoveAll(pyDir)
	if err := os.MkdirAll(pyDir, 0o755); err != nil {
		return "", err
	}
	zipPath := filepath.Join(pyDir, "python-embed.zip")
	var last error
	for _, url := range pyURLs {
		fmt.Printf("  trying %s\n", url)
		last = download(url, zipPath)
		if last != nil {
			fmt.Printf("  download failed: %v\n", last)
			continue
		}
		if last = unzip(zipPath, pyDir); last != nil {
			fmt.Printf("  unzip failed: %v\n", last)
			continue
		}
		break
	}
	_ = os.Remove(zipPath)
	if last != nil {
		if wp := tryWinget(); wp != "" {
			return wp, nil
		}
		return "", last
	}
	if err := enableSite(pyDir); err != nil {
		return "", err
	}
	if !pythonWorks(exe) {
		if wp := tryWinget(); wp != "" {
			return wp, nil
		}
		return "", fmt.Errorf("portable python.exe did not start after unzip")
	}
	fmt.Println("  Portable Python is ready.")
	return exe, nil
}

func pythonWorks(exe string) bool {
	st, err := os.Stat(exe)
	if err != nil || st.Size() == 0 {
		return false
	}
	cmd := exec.Command(exe, "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)")
	cmd.Env = append(os.Environ(), "PYTHONUTF8=1")
	return cmd.Run() == nil
}

func systemPython() string {
	for _, c := range [][]string{
		{"py", "-3"},
		{"python"},
		{"python3"},
	} {
		args := append([]string{}, c...)
		args = append(args, "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)")
		cmd := exec.Command(args[0], args[1:]...)
		if cmd.Run() != nil {
			continue
		}
		path, err := exec.LookPath(c[0])
		if err != nil {
			return c[0]
		}
		return path
	}
	return ""
}

func tryWinget() string {
	fmt.Println("  Trying winget to install Python 3.12 for this user...")
	cmd := exec.Command("winget", "install", "-e", "--id", "Python.Python.3.12",
		"--accept-package-agreements", "--accept-source-agreements", "--scope", "user", "--disable-interactivity")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	_ = cmd.Run()
	return systemPython()
}

func download(url, dest string) error {
	client := &http.Client{Timeout: 4 * time.Minute}
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return err
	}
	req.Header.Set("User-Agent", "FndZlda-installer/1.1")
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return fmt.Errorf("download HTTP %d", resp.StatusCode)
	}
	f, err := os.Create(dest)
	if err != nil {
		return err
	}
	defer f.Close()
	n, err := io.Copy(f, resp.Body)
	if err != nil {
		return err
	}
	if n < 1_000_000 {
		return fmt.Errorf("download too small (%d bytes)", n)
	}
	fmt.Printf("  downloaded %d MB\n", n/1024/1024)
	return nil
}

func unzip(src, dest string) error {
	r, err := zip.OpenReader(src)
	if err != nil {
		return err
	}
	defer r.Close()
	for _, f := range r.File {
		out := filepath.Join(dest, f.Name)
		cleanDest := filepath.Clean(dest) + string(os.PathSeparator)
		if !strings.HasPrefix(filepath.Clean(out)+string(os.PathSeparator), cleanDest) && filepath.Clean(out) != filepath.Clean(dest) {
			return fmt.Errorf("bad zip path %s", f.Name)
		}
		if f.FileInfo().IsDir() {
			if err := os.MkdirAll(out, 0o755); err != nil {
				return err
			}
			continue
		}
		if err := os.MkdirAll(filepath.Dir(out), 0o755); err != nil {
			return err
		}
		rc, err := f.Open()
		if err != nil {
			return err
		}
		w, err := os.OpenFile(out, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o644)
		if err != nil {
			rc.Close()
			return err
		}
		_, err = io.Copy(w, rc)
		w.Close()
		rc.Close()
		if err != nil {
			return err
		}
	}
	return nil
}

func enableSite(pyDir string) error {
	_ = os.MkdirAll(filepath.Join(pyDir, "Lib", "site-packages"), 0o755)
	matches, _ := filepath.Glob(filepath.Join(pyDir, "python*._pth"))
	body := "python312.zip\n.\nLib\nLib\\site-packages\nimport site\n"
	for _, p := range matches {
		name := strings.ToLower(filepath.Base(p))
		switch {
		case strings.Contains(name, "311"):
			body = "python311.zip\n.\nLib\nLib\\site-packages\nimport site\n"
		case strings.Contains(name, "313"):
			body = "python313.zip\n.\nLib\nLib\\site-packages\nimport site\n"
		case strings.Contains(name, "314"):
			body = "python314.zip\n.\nLib\nLib\\site-packages\nimport site\n"
		default:
			body = "python312.zip\n.\nLib\nLib\\site-packages\nimport site\n"
		}
		if err := os.WriteFile(p, []byte(body), 0o644); err != nil {
			return err
		}
	}
	if len(matches) == 0 {
		return os.WriteFile(filepath.Join(pyDir, "python312._pth"), []byte(body), 0o644)
	}
	return nil
}

func fail(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "\n  FndZlda: "+format+"\n", args...)
	fmt.Fprintln(os.Stderr, "  press Enter to close")
	fmt.Scanln()
	os.Exit(1)
}
