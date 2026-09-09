// FndZlda Windows launcher.
// Double-click: installs an embedded copy of the app plus portable Python
// (no admin, no PATH surgery) and starts the hunter in this console.
package main

import (
	"archive/zip"
	"bytes"
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

const pyURL = "https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip"

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
		fail("could not install Python: %v\n  Download Python yourself from https://www.python.org/downloads/\n  Check 'Add python.exe to PATH', then run FndZlda.exe again.", err)
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
	// Keep files the hunter already pulled from GitHub. First run unpacks the embed.
	if st, err := os.Stat(filepath.Join(pkg, "__init__.py")); err == nil && st.Size() > 0 {
		fmt.Println("  Hunter already on disk.")
		return nil
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
	if st, err := os.Stat(exe); err == nil && st.Size() > 0 {
		fmt.Println("  Python already on disk.")
		return exe, nil
	}
	fmt.Println("  No Python yet. Downloading a portable copy (US python.org)...")
	if err := os.MkdirAll(pyDir, 0o755); err != nil {
		return "", err
	}
	zipPath := filepath.Join(pyDir, "python-embed.zip")
	if err := download(pyURL, zipPath); err != nil {
		return "", err
	}
	if err := unzip(zipPath, pyDir); err != nil {
		return "", err
	}
	_ = os.Remove(zipPath)
	if err := enableSite(pyDir); err != nil {
		return "", err
	}
	if _, err := os.Stat(exe); err != nil {
		return "", fmt.Errorf("python.exe missing after unzip")
	}
	fmt.Println("  Portable Python is ready.")
	return exe, nil
}

func download(url, dest string) error {
	client := &http.Client{Timeout: 3 * time.Minute}
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return err
	}
	req.Header.Set("User-Agent", "FndZlda-installer")
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
		if !strings.HasPrefix(filepath.Clean(out), filepath.Clean(dest)+string(os.PathSeparator)) && filepath.Clean(out) != filepath.Clean(dest) {
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
	matches, _ := filepath.Glob(filepath.Join(pyDir, "python*._pth"))
	for _, p := range matches {
		b, err := os.ReadFile(p)
		if err != nil {
			return err
		}
		s := string(b)
		s = strings.ReplaceAll(s, "#import site", "import site")
		if !bytes.Contains([]byte(s), []byte("import site")) {
			s += "\nimport site\n"
		}
		if err := os.WriteFile(p, []byte(s), 0o644); err != nil {
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
