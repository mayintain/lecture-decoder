import importlib.util
import os
import platform
import shutil
import multiprocessing


def is_package_available(package_name: str) -> bool:
    return importlib.util.find_spec(package_name) is not None


def has_nvidia_gpu() -> bool:
    """
    Safe NVIDIA detection.

    We only check that nvidia-smi exists.
    This does NOT mean CUDA mode is ready.
    CUDA still requires correct drivers/libraries.
    """
    return shutil.which("nvidia-smi") is not None


def calculate_cpu_threads() -> int:
    """
    Safe CPU preset for faster-whisper CPU mode.

    Rule:
    - use about half of logical CPU cores
    - never less than 2
    - never more than 8

    This keeps the app responsive and avoids overheating laptops.
    """
    try:
        total_cores = multiprocessing.cpu_count()
        optimal_threads = total_cores // 2
        return max(2, min(optimal_threads, 8))
    except Exception:
        return 4


def get_system_profile() -> dict:
    system = platform.system()
    machine = platform.machine().lower()

    is_macos = system == "Darwin"
    is_windows = system == "Windows"
    is_linux = system == "Linux"

    is_arm = machine in ("arm64", "aarch64")
    is_x86 = machine in ("x86_64", "amd64", "i386", "i686")

    is_apple_silicon = is_macos and is_arm
    is_mac_intel = is_macos and is_x86
    is_windows_arm = is_windows and is_arm
    is_linux_arm = is_linux and is_arm

    mlx_available = is_package_available("mlx_whisper")
    faster_whisper_available = is_package_available("faster_whisper")
    nvidia_detected = has_nvidia_gpu()

    requested_engine = os.getenv("WHISPER_ENGINE", "auto")

    selected_engine = choose_engine(
        requested_engine=requested_engine,
        is_apple_silicon=is_apple_silicon,
        mlx_available=mlx_available,
        faster_whisper_available=faster_whisper_available
    )

    cpu_threads = None
    compute_type = None
    device = None

    if selected_engine == "faster_whisper":
        device = "cpu"
        compute_type = "int8"
        cpu_threads = calculate_cpu_threads()

    if selected_engine == "mlx_whisper":
        device = "mlx"
        compute_type = None
        cpu_threads = None

    return {
        "system": system,
        "machine": machine,

        "is_macos": is_macos,
        "is_windows": is_windows,
        "is_linux": is_linux,

        "is_arm": is_arm,
        "is_x86": is_x86,

        "is_apple_silicon": is_apple_silicon,
        "is_mac_intel": is_mac_intel,
        "is_windows_arm": is_windows_arm,
        "is_linux_arm": is_linux_arm,

        "mlx_available": mlx_available,
        "faster_whisper_available": faster_whisper_available,
        "nvidia_detected": nvidia_detected,
        "cuda_auto_enabled": False,

        "requested_engine": requested_engine,
        "selected_engine": selected_engine,

        "device": device,
        "compute_type": compute_type,
        "cpu_threads": cpu_threads,

        "platform_label": get_platform_label(
            is_apple_silicon=is_apple_silicon,
            is_mac_intel=is_mac_intel,
            is_windows=is_windows,
            is_linux=is_linux,
            is_windows_arm=is_windows_arm,
            is_linux_arm=is_linux_arm,
            machine=machine
        ),
        "engine_label": get_engine_label(selected_engine),
        "is_experimental_platform": is_windows_arm or is_linux_arm,
    }


def choose_engine(
    requested_engine: str,
    is_apple_silicon: bool,
    mlx_available: bool,
    faster_whisper_available: bool
) -> str:
    """
    Engine selection for MVP.

    auto:
    - Apple Silicon + mlx_whisper → mlx_whisper
    - everything else → faster_whisper CPU

    CUDA is intentionally NOT enabled automatically.
    """
    if requested_engine != "auto":
        return requested_engine

    if is_apple_silicon and mlx_available:
        return "mlx_whisper"

    if faster_whisper_available:
        return "faster_whisper"

    raise RuntimeError(
        "No available transcription engine found. "
        "Install mlx-whisper on Apple Silicon or faster-whisper as fallback."
    )


def get_platform_label(
    is_apple_silicon: bool,
    is_mac_intel: bool,
    is_windows: bool,
    is_linux: bool,
    is_windows_arm: bool,
    is_linux_arm: bool,
    machine: str
) -> str:
    if is_apple_silicon:
        return "Apple Silicon"

    if is_mac_intel:
        return "Mac Intel"

    if is_windows_arm:
        return "Windows ARM64 experimental"

    if is_windows:
        return "Windows"

    if is_linux_arm:
        return "Linux ARM64 experimental"

    if is_linux:
        return "Linux"

    return machine


def get_engine_label(engine: str) -> str:
    if engine == "mlx_whisper":
        return "MLX"

    if engine == "faster_whisper":
        return "faster-whisper CPU"

    return engine


def get_selected_engine() -> str:
    return get_system_profile()["selected_engine"]


def get_faster_whisper_runtime_config() -> dict:
    """
    Runtime config for FasterWhisperEngine.
    """
    profile = get_system_profile()

    return {
        "device": profile["device"] or "cpu",
        "compute_type": profile["compute_type"] or "int8",
        "cpu_threads": profile["cpu_threads"] or 4,
        "nvidia_detected": profile["nvidia_detected"],
        "cuda_auto_enabled": profile["cuda_auto_enabled"],
    }
