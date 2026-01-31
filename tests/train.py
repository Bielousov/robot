import os, signal, sys

# Set the path for the v3 directory
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from v3.models import train 

def _graceful_shutdown(signum, frame):
    print(f"\n[__train__] Received signal {signum}, stopping training…")
    train.stop()

signal.signal(signal.SIGINT, _graceful_shutdown)
signal.signal(signal.SIGTERM, _graceful_shutdown)

def _format_duration(seconds: float) -> str:
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}h {m}m {s}s"

def main():
    try:
        train.run()
    except KeyboardInterrupt:
        train.stop()
    finally:
        runtime = train.get_runtime_seconds()
        print(f"[__train__] Total runtime: {_format_duration(runtime)}")
        print("[__train__] Shutdown complete")
        sys.exit(0)

if __name__ == "__main__":
    main()
