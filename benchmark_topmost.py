"""
DeepPenny 置顶定时器性能测试
测量: CPU 占用率 + SetWindowPos 调用延迟
日志输出到文件 benchmark_debug.log (UTF-8) 避免终端编码问题
"""

import logging
import sys
import time
import statistics
from pathlib import Path

import psutil
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from ui.floating_window import FloatingWindow, _user32, _HWND_TOPMOST
from ui.floating_window import _SWP_NOMOVE, _SWP_NOSIZE, _SWP_NOACTIVATE

SAMPLE_INTERVAL = 0.2
PHASE_SAMPLES = 50
LOG_FILE = Path("benchmark_debug.log")
REPORT_FILE = Path("benchmark_report.txt")


def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    fh = logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    ))
    root.addHandler(fh)

    ui_logger = logging.getLogger("DeepPenny.ui")
    ui_logger.setLevel(logging.DEBUG)

    logging.getLogger("DeepPenny").setLevel(logging.DEBUG)


def log(msg: str):
    logging.getLogger("DeepPenny.benchmark").info(msg)
    print(msg)


def main():
    setup_logging()
    log("=== DeepPenny 置顶定时器性能测试 ===")
    log(f"日志文件: {LOG_FILE.resolve()}")
    log(f"报告文件: {REPORT_FILE.resolve()}")
    log("")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    config = {"refresh_interval": 3600, "snap_offset": 300}
    from api.deepseek_api import DeepSeekAPI
    api = DeepSeekAPI(api_key="")
    window = FloatingWindow(config, api)
    window.show()

    proc = psutil.Process()
    proc.cpu_percent(interval=0.0)

    samples_on = []
    latencies = []
    samples_off = []
    phase = 0

    def measure_latency():
        hwnd = int(window.winId())
        log("开始测量 SetWindowPos 延迟 (1000次)...")
        for i in range(1000):
            t0 = time.perf_counter_ns()
            _user32.SetWindowPos(
                hwnd, _HWND_TOPMOST, 0, 0, 0, 0,
                _SWP_NOMOVE | _SWP_NOSIZE | _SWP_NOACTIVATE,
            )
            elapsed_us = (time.perf_counter_ns() - t0) / 1000
            latencies.append(elapsed_us)
        log(f"延迟测量完成, 平均 {statistics.mean(latencies):.2f} us")

        nonlocal phase
        phase = 3
        log("Phase 2: 定时器关 (对比基准)...")
        window._topmost_timer.stop()

    def sample():
        nonlocal phase
        if phase == 0:
            phase = 1
            log("Phase 1: 定时器开 (200ms) - 采样 CPU 中...")
            samples_on.clear()
            latencies.clear()
            samples_off.clear()
            samples_on.append(proc.cpu_percent(interval=0.0))
            return

        if phase == 1:
            cpu = proc.cpu_percent(interval=0.0)
            samples_on.append(cpu)
            if len(samples_on) >= PHASE_SAMPLES:
                phase = 2
                log(f"CPU 采样完成 (Timer ON), 平均 {sum(samples_on)/len(samples_on):.3f}%")
                QTimer.singleShot(0, measure_latency)
                return

        if phase == 3:
            cpu = proc.cpu_percent(interval=0.0)
            samples_off.append(cpu)
            if len(samples_off) >= PHASE_SAMPLES:
                phase = 4
                log(f"CPU 采样完成 (Timer OFF), 平均 {sum(samples_off)/len(samples_off):.3f}%")
                QTimer.singleShot(0, report_and_exit)
                return

    def report_and_exit():
        lines = []
        def wl(text=""):
            lines.append(text)

        wl()
        wl("=" * 60)
        wl("  ***  Performance Report ***")
        wl("=" * 60)
        wl()

        def add_stats(label, data, unit="%"):
            avg = sum(data) / len(data)
            wl(f"  {label}")
            wl(f"  |  Samples:  {len(data)}")
            wl(f"  |  Average:  {avg:.3f} {unit}")
            wl(f"  |  Max:      {max(data):.3f} {unit}")
            if len(data) > 1:
                wl(f"  |  StdDev:   {statistics.stdev(data):.3f} {unit}")
            wl()

        add_stats("[Timer ON]  timer active (200ms interval)", samples_on)
        add_stats("[Timer OFF] timer stopped (baseline)", samples_off)

        avg_on = sum(samples_on) / len(samples_on)
        avg_off = sum(samples_off) / len(samples_off)
        diff = avg_on - avg_off
        wl(f"  [CPU]  Delta (ON - OFF): {diff:+.3f}%")
        if diff < 0.5:
            wl(f"    -> Negligible (< 0.5%)")
        elif diff < 2:
            wl(f"    -> Mild (0.5% ~ 2%)")
        else:
            wl(f"    -> Significant (> 2%)")
        wl()

        avg_lat = statistics.mean(latencies)
        median_lat = statistics.median(latencies)
        sorted_lats = sorted(latencies)
        p50 = sorted_lats[int(len(latencies) * 0.50) - 1]
        p99 = sorted_lats[int(len(latencies) * 0.99) - 1]
        wl(f"  [LATENCY]  SetWindowPos (1000 calls)")
        wl(f"  |  Average:  {avg_lat:.2f} us")
        wl(f"  |  Median:   {median_lat:.2f} us")
        wl(f"  |  P50:      {p50:.2f} us")
        wl(f"  |  P99:      {p99:.2f} us")
        wl(f"  |  Min:      {min(latencies):.2f} us")
        wl(f"  |  Max:      {max(latencies):.2f} us")
        wl(f"  |  Cost@5Hz: {avg_lat * 5 / 1000:.3f} ms/sec")
        wl()

        wl("=" * 60)
        wl("  [DONE]")
        wl("=" * 60)

        report = "\n".join(lines)

        print()
        print(report)
        print(f"\n详细日志已保存至: {LOG_FILE.resolve()}")

        REPORT_FILE.write_text(report, encoding="utf-8")
        print(f"报告已保存至: {REPORT_FILE.resolve()}")

        QApplication.quit()

    timer = QTimer()
    timer.timeout.connect(sample)
    timer.start(int(SAMPLE_INTERVAL * 1000))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
