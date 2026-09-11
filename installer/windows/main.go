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

//go:embed payload/fndzlda/*.py payload/fndzlda/*.txt payload/fndzlda/*.wav payload/fndzlda/*.mp3 payload/fndzlda/*.b64
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

	n, err := extractApp(appDir)
	if err != nil {
		fail("could not unpack the hunter: %v", err)
	}
	if n < 3 {
		fail("hunter package missing after unpack (%d files in %s)", n, filepath.Join(appDir, "fndzlda"))
	}
	fmt.Printf("  unpacked %d hunter files\n", n)
	downloadSounds(filepath.Join(appDir, "fndzlda"))

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

func extractApp(appDir string) (int, error) {
	pkg := filepath.Join(appDir, "fndzlda")
	if err := os.MkdirAll(pkg, 0o755); err != nil {
		return 0, err
	}
	written := 0
	err := fs.WalkDir(payload, "payload/fndzlda", func(path string, d fs.DirEntry, err error) error {
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
		if err := os.WriteFile(filepath.Join(pkg, name), b, 0o644); err != nil {
			return err
		}
		written++
		return nil
	})
	if err != nil {
		return written, err
	}
	need := []string{"__init__.py", "__main__.py"}
	for _, n := range need {
		if _, err := os.Stat(filepath.Join(pkg, n)); err != nil {
			return written, fmt.Errorf("missing %s after unpack", n)
		}
	}
	return written, nil
}

func downloadSounds(pkg string) {
	files := []string{"listen.wav", "storms.mp3"}
	base := "https://raw.githubusercontent.com/Memberoffoxhound/FndZlda/main/fndzlda/"
	for _, name := range files {
		dest := filepath.Join(pkg, name)
		if st, err := os.Stat(dest); err == nil && st.Size() > 200 {
			continue
		}
		fmt.Printf("  downloading %s\n", name)
		if err := downloadFile(base+name, dest, 200); err != nil {
			fmt.Printf("  %s not on GitHub yet (%v)\n", name, err)
		}
	}
}

func writeRunner(appDir string) (string, error) {
	p := filepath.Join(appDir, "run_hunter.py")
	body := "import sys\nfrom pathlib import Path\nroot = Path(__file__).resolve().parent\nsys.path.insert(0, str(root))\nfrom fndzlda.__main__ import main\nraise SystemExit(main())\n"
	return p, os.WriteFile(p, []byte(body), 0o644)
}

func ensurePython(pyDir, appDir string) (string, error) {
	exe := filepath.Join(pyDir, "python.exe")
	if pythonWorks(exe) {
		_ = enableSite(pyDir, appDir)
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
			_ = enableSite(pyDir, appDir)
			return wp, nil
		}
		return "", last
	}
	if err := enableSite(pyDir, appDir); err != nil {
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
	return downloadFile(url, dest, 1_000_000)
}

func downloadFile(url, dest string, min int64) error {
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
	if n < min {
		return fmt.Errorf("download too small (%d bytes)", n)
	}
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

func enableSite(pyDir, appDir string) error {
	_ = os.MkdirAll(filepath.Join(pyDir, "Lib", "site-packages"), 0o755)
	zipName := "python312.zip"
	matches, _ := filepath.Glob(filepath.Join(pyDir, "python*._pth"))
	for _, p := range matches {
		name := strings.ToLower(filepath.Base(p))
		switch {
		case strings.Contains(name, "311"):
			zipName = "python311.zip"
		case strings.Contains(name, "313"):
			zipName = "python313.zip"
		case strings.Contains(name, "314"):
			zipName = "python314.zip"
		default:
			zipName = "python312.zip"
		}
	}
	app := filepath.ToSlash(appDir)
	body := zipName + "\n.\nLib\nLib\\site-packages\n" + app + "\nimport site\n"
	if len(matches) == 0 {
		return os.WriteFile(filepath.Join(pyDir, "python312._pth"), []byte(body), 0o644)
	}
	for _, p := range matches {
		if err := os.WriteFile(p, []byte(body), 0o644); err != nil {
			return err
		}
	}
	return nil
}

func fail(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "\n  FndZlda: "+format+"\n", args...)
	fmt.Fprintln(os.Stderr, "  press Enter to close")
	fmt.Scanln()
	os.Exit(1)
}
