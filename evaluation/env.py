"""Umgebungsdaten: auf welchem Gerät mit welcher Software wurde gemessen?

Absolute Zeiten hängen von Hardware und Software ab. Deshalb werden diese Angaben zu jeder
Messreihe gespeichert (JSON neben den CSV-Dateien) und gehören in den Versuchsaufbau der Arbeit.
"""
import datetime
import importlib.metadata as md
import os
import platform
import subprocess
import sys


def _run(cmd, cwd=None):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=5, cwd=cwd)
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


def cpu_model():
    """Name des Prozessors (macOS, Linux, sonst Platform-Angabe)."""
    system = platform.system()
    if system == "Darwin":
        return _run(["sysctl", "-n", "machdep.cpu.brand_string"]) or platform.processor()
    if system == "Linux":
        try:
            with open("/proc/cpuinfo", encoding="utf-8") as f:
                for line in f:
                    if line.lower().startswith("model name"):
                        return line.split(":", 1)[1].strip()
        except OSError:
            pass
    return platform.processor() or "unbekannt"


def package_version(name):
    try:
        return md.version(name)
    except md.PackageNotFoundError:
        return None


def clock_resolution():
    """Auflösung der verwendeten Uhren in Nanosekunden (wichtig für sehr kurze Läufe)."""
    import time
    return {
        "perf_counter_ns": int(time.get_clock_info("perf_counter").resolution * 1e9),
        "process_time_ns": int(time.get_clock_info("process_time").resolution * 1e9),
    }


def collect_environment(repo_path=None):
    """Sammelt alles, was für die Einordnung absoluter Zeiten nötig ist."""
    info = {
        "zeitpunkt": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "betriebssystem": f"{platform.system()} {platform.release()}",
        "os_version": platform.version(),
        "rechner": platform.machine(),
        "cpu": cpu_model(),
        "logische_kerne": os.cpu_count(),
        "python": sys.version.split()[0],
        "python_implementierung": platform.python_implementation(),
        "py_sudoku": package_version("py-sudoku"),
        "pandas": package_version("pandas"),
        "numpy": package_version("numpy"),
        "uhren_aufloesung": clock_resolution(),
    }
    try:
        info["last_beim_start_1min"] = round(os.getloadavg()[0], 2)
    except (AttributeError, OSError):
        info["last_beim_start_1min"] = None
    if repo_path:
        info["git_commit"] = _run(["git", "rev-parse", "HEAD"], cwd=repo_path)
        status = _run(["git", "status", "--porcelain"], cwd=repo_path)
        info["git_unsauber"] = bool(status) if status is not None else None
    # Dinge, die ein Programm nicht sicher herausfinden kann: vom Messenden einzutragen
    info["manuell_eintragen"] = {
        "netzbetrieb": None,
        "energiesparmodus_aus": None,
        "andere_programme_geschlossen": None,
    }
    return info
