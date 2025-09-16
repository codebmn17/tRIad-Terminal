#!/usr/bin/env python3

"""
Triad Terminal Monitoring Dashboard
Provides real-time monitoring of applications and system resources
"""

import datetime
import logging
import os
import threading
import time
from typing import Any

import psutil

# Optional imports for enhanced visualization
try:
    import dash
    import dash_core_components as dcc
    import dash_html_components as html
    import plotly.graph_objs as go
    from dash.dependencies import Input, Output

    HAS_DASH = True
except ImportError:
    HAS_DASH = False

# For terminal-based UI as fallback
try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.table import Table

    HAS_RICH = True
except ImportError:
    HAS_RICH = False

logger = logging.getLogger("triad.monitor")


class SystemMonitor:
    """Monitor system resources and performance metrics"""

    def __init__(self, interval: float = 2.0):
        self.interval = interval
        self.running = False
        self.thread = None
        self.history_length = 60  # Keep last 60 data points

        # Initialize metric history
        self.metrics_history = {"cpu": [], "memory": [], "disk": [], "network": [], "processes": []}

        # Latest metrics
        self.current_metrics = {"cpu": {}, "memory": {}, "disk": {}, "network": {}, "processes": {}}

    def start(self) -> bool:
        """Start monitoring in background thread"""
        if self.running:
            return True

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        return True

    def stop(self) -> bool:
        """Stop monitoring"""
        if not self.running:
            return True

        self.running = False
        if self.thread:
            self.thread.join(timeout=3.0)

        return True

    def _monitor_loop(self) -> None:
        """Background thread to collect metrics"""
        while self.running:
            try:
                metrics = self._collect_metrics()

                # Store current metrics
                self.current_metrics = metrics

                # Add to history
                for category in self.metrics_history:
                    if category in metrics:
                        self.metrics_history[category].append(
                            {
                                "timestamp": datetime.datetime.now().isoformat(),
                                "data": metrics[category],
                            }
                        )

                        # Trim history to keep only recent data
                        if len(self.metrics_history[category]) > self.history_length:
                            self.metrics_history[category] = self.metrics_history[category][
                                -self.history_length :
                            ]

                # Sleep for interval
                time.sleep(self.interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.interval)

    def _collect_metrics(self) -> dict[str, Any]:
        """Collect system metrics"""
        metrics = {}

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        cpu_stats = psutil.cpu_stats()

        metrics["cpu"] = {
            "percent": cpu_percent,
            "percent_average": sum(cpu_percent) / len(cpu_percent) if cpu_percent else 0,
            "count": psutil.cpu_count(),
            "frequency": {
                "current": cpu_freq.current if cpu_freq else None,
                "min": cpu_freq.min if cpu_freq and hasattr(cpu_freq, "min") else None,
                "max": cpu_freq.max if cpu_freq and hasattr(cpu_freq, "max") else None,
            },
            "stats": {
                "ctx_switches": cpu_stats.ctx_switches,
                "interrupts": cpu_stats.interrupts,
                "soft_interrupts": cpu_stats.soft_interrupts,
                "syscalls": cpu_stats.syscalls,
            },
        }

        # Memory metrics
        virtual_mem = psutil.virtual_memory()
        swap_mem = psutil.swap_memory()

        metrics["memory"] = {
            "virtual": {
                "total": virtual_mem.total,
                "available": virtual_mem.available,
                "used": virtual_mem.used,
                "percent": virtual_mem.percent,
            },
            "swap": {
                "total": swap_mem.total,
                "used": swap_mem.used,
                "free": swap_mem.free,
                "percent": swap_mem.percent,
            },
        }

        # Disk metrics
        metrics["disk"] = {}

        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)

                metrics["disk"][partition.mountpoint] = {
                    "device": partition.device,
                    "fstype": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent,
                }
            except PermissionError:
                # Some mountpoints might not be accessible
                pass

        # Disk IO counters
        try:
            disk_io = psutil.disk_io_counters()
            metrics["disk"]["io"] = {
                "read_count": disk_io.read_count,
                "write_count": disk_io.write_count,
                "read_bytes": disk_io.read_bytes,
                "write_bytes": disk_io.write_bytes,
                "read_time": disk_io.read_time,
                "write_time": disk_io.write_time,
            }
        except:
            metrics["disk"]["io"] = {}

        # Network metrics
        try:
            net_io = psutil.net_io_counters()

            metrics["network"] = {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errin": net_io.errin,
                "errout": net_io.errout,
                "dropin": net_io.dropin,
                "dropout": net_io.dropout,
            }

            # Add per-interface stats
            metrics["network"]["interfaces"] = {}

            for name, stats in psutil.net_if_stats().items():
                metrics["network"]["interfaces"][name] = {
                    "isup": stats.isup,
                    "duplex": stats.duplex,
                    "speed": stats.speed,
                    "mtu": stats.mtu,
                }
        except:
            metrics["network"] = {}

        # Process metrics
        metrics["processes"] = {}

        # Get total process count
        metrics["processes"]["count"] = len(psutil.pids())

        # Get top processes by memory and CPU
        processes = []
        for proc in psutil.process_iter(
            ["pid", "name", "username", "memory_percent", "cpu_percent"]
        ):
            try:
                proc_info = proc.info
                # Try to get more info
                proc_info["cmdline"] = proc.cmdline()
                proc_info["status"] = proc.status()

                if proc_info["cpu_percent"] > 0.1 or proc_info["memory_percent"] > 0.1:
                    processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

        # Sort by memory usage (descending)
        processes.sort(key=lambda x: x.get("memory_percent", 0), reverse=True)
        metrics["processes"]["top_memory"] = processes[:10]

        # Sort by CPU usage (descending)
        processes.sort(key=lambda x: x.get("cpu_percent", 0), reverse=True)
        metrics["processes"]["top_cpu"] = processes[:10]

        return metrics

    def get_latest_metrics(self) -> dict[str, Any]:
        """Get the latest metrics"""
        return self.current_metrics

    def get_metrics_history(self) -> dict[str, list[dict[str, Any]]]:
        """Get historical metrics"""
        return self.metrics_history


class ApplicationMonitor:
    """Monitor specific applications and their performance"""

    def __init__(self, interval: float = 5.0):
        self.interval = interval
        self.running = False
        self.thread = None
        self.applications = {}  # Applications to monitor
        self.metrics = {}  # Current metrics
        self.history = {}  # Historical metrics
        self.history_length = 30  # Keep last 30 data points

    def add_application(self, name: str, config: dict[str, Any]) -> bool:
        """Add an application to monitor

        config can have:
        - pid: Process ID to monitor
        - process_name: Process name to monitor
        - port: Port to check for HTTP healthcheck
        - url: URL to check for HTTP healthcheck
        - log_file: Log file to monitor
        """
        self.applications[name] = config
        self.metrics[name] = {"status": "unknown"}
        self.history[name] = []
        return True

    def remove_application(self, name: str) -> bool:
        """Remove an application from monitoring"""
        if name in self.applications:
            del self.applications[name]

            if name in self.metrics:
                del self.metrics[name]

            if name in self.history:
                del self.history[name]

            return True
        return False

    def start(self) -> bool:
        """Start monitoring applications"""
        if self.running:
            return True

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        return True

    def stop(self) -> bool:
        """Stop monitoring applications"""
        if not self.running:
            return True

        self.running = False
        if self.thread:
            self.thread.join(timeout=3.0)

        return True

    def _monitor_loop(self) -> None:
        """Background thread to monitor applications"""
        while self.running:
            try:
                # Check each application
                for name, config in self.applications.items():
                    try:
                        metrics = self._check_application(name, config)

                        # Store current metrics
                        self.metrics[name] = metrics

                        # Add to history
                        self.history[name].append(
                            {"timestamp": datetime.datetime.now().isoformat(), "data": metrics}
                        )

                        # Trim history to keep only recent data
                        if len(self.history[name]) > self.history_length:
                            self.history[name] = self.history[name][-self.history_length :]

                    except Exception as e:
                        logger.error(f"Error checking application {name}: {e}")
                        self.metrics[name] = {"status": "error", "error": str(e)}

                # Sleep for interval
                time.sleep(self.interval)

            except Exception as e:
                logger.error(f"Error in application monitoring loop: {e}")
                time.sleep(self.interval)

    def _check_application(self, name: str, config: dict[str, Any]) -> dict[str, Any]:
        """Check a single application's status"""
        metrics = {"status": "unknown"}

        # Check by PID
        if "pid" in config:
            try:
                pid = config["pid"]
                process = psutil.Process(pid)

                # Get process info
                metrics["process"] = {
                    "pid": pid,
                    "name": process.name(),
                    "status": process.status(),
                    "cpu_percent": process.cpu_percent(interval=0.1),
                    "memory_percent": process.memory_percent(),
                    "memory_info": {
                        "rss": process.memory_info().rss,
                        "vms": process.memory_info().vms,
                    },
                    "threads": len(process.threads()),
                    "connections": len(process.connections()),
                }

                metrics["status"] = "running"
            except psutil.NoSuchProcess:
                metrics["status"] = "not_running"
                metrics["error"] = f"Process with PID {pid} not found"

        # Check by process name
        elif "process_name" in config:
            try:
                process_name = config["process_name"]
                matching_processes = []

                for process in psutil.process_iter(["pid", "name", "cmdline"]):
                    try:
                        # Check if process name matches
                        if process.info["name"] == process_name or (
                            process.info["cmdline"]
                            and any(process_name in cmd for cmd in process.info["cmdline"])
                        ):

                            proc_info = {
                                "pid": process.pid,
                                "name": process.name(),
                                "status": process.status(),
                                "cpu_percent": process.cpu_percent(interval=0.1),
                                "memory_percent": process.memory_percent(),
                                "memory_info": {
                                    "rss": process.memory_info().rss,
                                    "vms": process.memory_info().vms,
                                },
                                "threads": len(process.threads()),
                            }
                            matching_processes.append(proc_info)

                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                if matching_processes:
                    metrics["processes"] = matching_processes
                    metrics["status"] = "running"
                    metrics["count"] = len(matching_processes)
                else:
                    metrics["status"] = "not_running"
                    metrics["error"] = f"No processes matching '{process_name}' found"

            except Exception as e:
                metrics["status"] = "error"
                metrics["error"] = str(e)

        # Check by port (HTTP health check)
        elif "port" in config:
            try:
                import http.client
                import socket

                port = config["port"]
                host = config.get("host", "localhost")
                path = config.get("path", "/")

                # First check if port is open
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((host, port))
                sock.close()

                if result == 0:
                    # Port is open, try HTTP request
                    conn = http.client.HTTPConnection(host, port, timeout=5)
                    conn.request("GET", path)
                    response = conn.getresponse()

                    metrics["http"] = {"status_code": response.status, "reason": response.reason}

                    if 200 <= response.status < 400:
                        metrics["status"] = "healthy"
                    else:
                        metrics["status"] = "unhealthy"

                    conn.close()
                else:
                    metrics["status"] = "not_running"
                    metrics["error"] = f"Port {port} is closed"

            except Exception as e:
                metrics["status"] = "error"
                metrics["error"] = str(e)

        # Check by URL
        elif "url" in config:
            try:
                import requests

                url = config["url"]
                timeout = config.get("timeout", 5)

                response = requests.get(url, timeout=timeout)

                metrics["http"] = {
                    "status_code": response.status_code,
                    "response_time": response.elapsed.total_seconds(),
                }

                if 200 <= response.status_code < 400:
                    metrics["status"] = "healthy"
                else:
                    metrics["status"] = "unhealthy"

            except requests.RequestException as e:
                metrics["status"] = "error"
                metrics["error"] = str(e)

        # Check by log file
        elif "log_file" in config:
            try:
                log_file = config["log_file"]

                if os.path.exists(log_file):
                    # Get log file stats
                    stats = os.stat(log_file)

                    metrics["log"] = {
                        "size": stats.st_size,
                        "last_modified": datetime.datetime.fromtimestamp(
                            stats.st_mtime
                        ).isoformat(),
                    }

                    # Check for recent activity
                    now = time.time()
                    if now - stats.st_mtime < 3600:  # Modified in the last hour
                        metrics["status"] = "active"
                    else:
                        metrics["status"] = "inactive"

                    # Optionally check for errors in the log
                    if config.get("check_errors", False):
                        with open(log_file, encoding="utf-8", errors="ignore") as f:
                            # Read the last 100 lines
                            lines = f.readlines()[-100:]
                            error_count = sum(1 for line in lines if "error" in line.lower())
                            metrics["log"]["recent_errors"] = error_count

                else:
                    metrics["status"] = "not_found"
                    metrics["error"] = f"Log file {log_file} not found"

            except Exception as e:
                metrics["status"] = "error"
                metrics["error"] = str(e)

        return metrics

    def get_application_metrics(
        self, name: str | None = None
    ) -> dict[str, Any] | dict[str, dict[str, Any]]:
        """Get metrics for a specific application or all applications"""
        if name:
            return self.metrics.get(
                name, {"status": "unknown", "error": "Application not monitored"}
            )
        else:
            return self.metrics

    def get_application_history(
        self, name: str | None = None
    ) -> list[dict[str, Any]] | dict[str, list[dict[str, Any]]]:
        """Get historical metrics for a specific application or all applications"""
        if name:
            return self.history.get(name, [])
        else:
            return self.history


class DashboardServer:
    """Web dashboard for monitoring"""

    def __init__(
        self,
        system_monitor: SystemMonitor,
        app_monitor: ApplicationMonitor,
        host: str = "localhost",
        port: int = 8050,
    ):
        if not HAS_DASH:
            raise ImportError(
                "Dash is required for web dashboard. Install with: pip install dash plotly"
            )

        self.system_monitor = system_monitor
        self.app_monitor = app_monitor
        self.host = host
        self.port = port
        self.app = dash.Dash(__name__)
        self._setup_layout()
        self._setup_callbacks()

    def _setup_layout(self) -> None:
        """Set up the dashboard layout"""
        self.app.layout = html.Div(
            [
                html.H1("Triad Terminal Monitoring Dashboard"),
                html.Div(
                    [
                        html.Div(
                            [html.H2("System Overview"), html.Div(id="system-overview")],
                            className="row",
                        ),
                        html.Div(
                            [html.H2("CPU Usage"), dcc.Graph(id="cpu-graph")], className="row"
                        ),
                        html.Div(
                            [html.H2("Memory Usage"), dcc.Graph(id="memory-graph")], className="row"
                        ),
                        html.Div(
                            [html.H2("Network Traffic"), dcc.Graph(id="network-graph")],
                            className="row",
                        ),
                        html.Div(
                            [html.H2("Applications"), html.Div(id="applications-table")],
                            className="row",
                        ),
                        # Hidden div for storing data
                        html.Div(id="interval-component", style={"display": "none"}),
                        dcc.Interval(
                            id="refresh-interval",
                            interval=2 * 1000,  # in milliseconds
                            n_intervals=0,
                        ),
                    ]
                ),
            ]
        )

    def _setup_callbacks(self) -> None:
        """Set up the dashboard callbacks"""

        @self.app.callback(
            Output("interval-component", "children"), Input("refresh-interval", "n_intervals")
        )
        def update_metrics(_):
            # This callback doesn't need to do anything,
            # as the monitors are already updating their data
            return datetime.datetime.now().isoformat()

        @self.app.callback(
            Output("system-overview", "children"), Input("interval-component", "children")
        )
        def update_system_overview(_):
            metrics = self.system_monitor.get_latest_metrics()

            if not metrics:
                return html.Div("No system metrics available")

            # Format system overview
            cpu_percent = metrics.get("cpu", {}).get("percent_average", 0)
            memory_percent = metrics.get("memory", {}).get("virtual", {}).get("percent", 0)

            return html.Div(
                [
                    html.Div(
                        [
                            html.H4("CPU"),
                            html.Div(
                                f"{cpu_percent:.1f}%",
                                style={
                                    "fontSize": "24px",
                                    "color": (
                                        "#ff4136"
                                        if cpu_percent > 80
                                        else ("#ff851b" if cpu_percent > 50 else "#2ecc40")
                                    ),
                                },
                            ),
                        ],
                        className="four columns",
                    ),
                    html.Div(
                        [
                            html.H4("Memory"),
                            html.Div(
                                f"{memory_percent:.1f}%",
                                style={
                                    "fontSize": "24px",
                                    "color": (
                                        "#ff4136"
                                        if memory_percent > 80
                                        else ("#ff851b" if memory_percent > 50 else "#2ecc40")
                                    ),
                                },
                            ),
                        ],
                        className="four columns",
                    ),
                    html.Div(
                        [
                            html.H4("Processes"),
                            html.Div(
                                f"{metrics.get('processes', {}).get('count', 0)}",
                                style={"fontSize": "24px"},
                            ),
                        ],
                        className="four columns",
                    ),
                ],
                className="row",
            )

        @self.app.callback(Output("cpu-graph", "figure"), Input("interval-component", "children"))
        def update_cpu_graph(_):
            history = self.system_monitor.get_metrics_history()
            cpu_history = history.get("cpu", [])

            if not cpu_history:
                return go.Figure()

            # Extract data for graph
            times = [item["timestamp"] for item in cpu_history]
            cpu_avg = [item["data"]["percent_average"] for item in cpu_history]

            # Create the figure
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=cpu_avg,
                    mode="lines+markers",
                    name="CPU Average",
                    line=dict(color="#0074D9", width=2),
                )
            )

            fig.update_layout(
                title="CPU Usage Over Time",
                xaxis=dict(title="Time"),
                yaxis=dict(title="CPU %", range=[0, 100]),
                margin=dict(l=40, r=40, t=40, b=40),
            )

            return fig

        @self.app.callback(
            Output("memory-graph", "figure"), Input("interval-component", "children")
        )
        def update_memory_graph(_):
            history = self.system_monitor.get_metrics_history()
            memory_history = history.get("memory", [])

            if not memory_history:
                return go.Figure()

            # Extract data for graph
            times = [item["timestamp"] for item in memory_history]
            memory_percent = [item["data"]["virtual"]["percent"] for item in memory_history]
            swap_percent = [
                item["data"]["swap"]["percent"] for item in memory_history if "swap" in item["data"]
            ]

            # Create the figure
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=memory_percent,
                    mode="lines+markers",
                    name="Memory",
                    line=dict(color="#FF4136", width=2),
                )
            )

            if swap_percent and len(swap_percent) == len(times):
                fig.add_trace(
                    go.Scatter(
                        x=times,
                        y=swap_percent,
                        mode="lines+markers",
                        name="Swap",
                        line=dict(color="#FF851B", width=2),
                    )
                )

            fig.update_layout(
                title="Memory Usage Over Time",
                xaxis=dict(title="Time"),
                yaxis=dict(title="Memory %", range=[0, 100]),
                margin=dict(l=40, r=40, t=40, b=40),
            )

            return fig

        @self.app.callback(
            Output("network-graph", "figure"), Input("interval-component", "children")
        )
        def update_network_graph(_):
            history = self.system_monitor.get_metrics_history()
            network_history = history.get("network", [])

            if not network_history:
                return go.Figure()

            # Extract data for graph
            times = [item["timestamp"] for item in network_history]

            # Calculate network speeds between intervals
            bytes_sent = []
            bytes_recv = []

            for i in range(1, len(network_history)):
                prev = network_history[i - 1]["data"]
                curr = network_history[i]["data"]

                if "bytes_sent" in prev and "bytes_sent" in curr:
                    sent_diff = curr["bytes_sent"] - prev["bytes_sent"]
                    bytes_sent.append(sent_diff / self.system_monitor.interval / 1024)  # KB/s
                else:
                    bytes_sent.append(0)

                if "bytes_recv" in prev and "bytes_recv" in curr:
                    recv_diff = curr["bytes_recv"] - prev["bytes_recv"]
                    bytes_recv.append(recv_diff / self.system_monitor.interval / 1024)  # KB/s
                else:
                    bytes_recv.append(0)

            # Adjust times to match data points
            times = times[1:]

            # Create the figure
            fig = go.Figure()

            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=bytes_sent,
                    mode="lines+markers",
                    name="Upload (KB/s)",
                    line=dict(color="#3D9970", width=2),
                )
            )

            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=bytes_recv,
                    mode="lines+markers",
                    name="Download (KB/s)",
                    line=dict(color="#7FDBFF", width=2),
                )
            )

            fig.update_layout(
                title="Network Traffic",
                xaxis=dict(title="Time"),
                yaxis=dict(title="KB/s"),
                margin=dict(l=40, r=40, t=40, b=40),
            )

            return fig

        @self.app.callback(
            Output("applications-table", "children"), Input("interval-component", "children")
        )
        def update_applications_table(_):
            metrics = self.app_monitor.get_application_metrics()

            if not metrics:
                return html.Div("No applications being monitored")

            # Create table
            return html.Table(
                [
                    html.Thead(
                        html.Tr([html.Th("Application"), html.Th("Status"), html.Th("Details")])
                    ),
                    html.Tbody(
                        [
                            html.Tr(
                                [
                                    html.Td(name),
                                    html.Td(
                                        app["status"],
                                        style={
                                            "color": (
                                                "#ff4136"
                                                if app["status"] in ["error", "not_running"]
                                                else (
                                                    "#ffdc00"
                                                    if app["status"] in ["unhealthy", "inactive"]
                                                    else "#2ecc40"
                                                )
                                            )
                                        },
                                    ),
                                    html.Td(self._format_app_details(app)),
                                ]
                            )
                            for name, app in metrics.items()
                        ]
                    ),
                ],
                className="table",
            )

    def _format_app_details(self, app: dict[str, Any]) -> str:
        """Format application details for display"""
        if "error" in app:
            return app["error"]

        if "process" in app:
            return f"PID: {app['process']['pid']}, CPU: {app['process']['cpu_percent']:.1f}%, Memory: {app['process']['memory_percent']:.1f}%"

        if "http" in app:
            return f"HTTP Status: {app['http']['status_code']}"

        if "log" in app:
            return f"Log size: {app['log']['size'] // 1024} KB, Last modified: {app['log']['last_modified']}"

        return ""

    def start(self) -> None:
        """Start the dashboard server"""
        self.app.run_server(host=self.host, port=self.port, debug=False)


class TerminalDashboard:
    """Terminal-based monitoring dashboard"""

    def __init__(self, system_monitor: SystemMonitor, app_monitor: ApplicationMonitor):
        if not HAS_RICH:
            raise ImportError(
                "Rich is required for terminal dashboard. Install with: pip install rich"
            )

        self.system_monitor = system_monitor
        self.app_monitor = app_monitor
        self.console = Console()
        self.running = False

    def start(self) -> None:
        """Start the terminal dashboard"""
        self.running = True

        try:
            with Live(self._generate_layout(), refresh_per_second=0.5, screen=True) as live:
                while self.running:
                    live.update(self._generate_layout())
                    time.sleep(1)
        except KeyboardInterrupt:
            self.running = False

    def stop(self) -> None:
        """Stop the terminal dashboard"""
        self.running = False

    def _generate_layout(self) -> Layout:
        """Generate the dashboard layout"""
        layout = Layout()

        # Create header
        layout.split(Layout(name="header", size=3), Layout(name="main"))

        # Create title
        layout["header"].update(
            Panel(
                f"[bold blue]Triad Terminal Monitoring Dashboard[/] - [yellow]{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/]",
                style="blue",
            )
        )

        # Split main area
        layout["main"].split_row(Layout(name="system", ratio=1), Layout(name="apps", ratio=1))

        # Get metrics
        sys_metrics = self.system_monitor.get_latest_metrics()
        app_metrics = self.app_monitor.get_application_metrics()

        # Create system metrics panel
        cpu_percent = sys_metrics.get("cpu", {}).get("percent_average", 0)
        memory_percent = sys_metrics.get("memory", {}).get("virtual", {}).get("percent", 0)

        # Create CPU table
        cpu_table = Table(show_header=True, header_style="bold magenta")
        cpu_table.add_column("CPU Core")
        cpu_table.add_column("Usage %")

        cpu_cores = sys_metrics.get("cpu", {}).get("percent", [])
        for i, core in enumerate(cpu_cores):
            color = "green"
            if core > 80:
                color = "red"
            elif core > 50:
                color = "yellow"

            cpu_table.add_row(f"Core {i}", f"[{color}]{core:.1f}%[/]")

        # Create memory table
        memory_table = Table(show_header=True, header_style="bold magenta")
        memory_table.add_column("Memory")
        memory_table.add_column("Value")

        virtual_mem = sys_metrics.get("memory", {}).get("virtual", {})
        if virtual_mem:
            total_gb = virtual_mem.get("total", 0) / (1024**3)
            used_gb = virtual_mem.get("used", 0) / (1024**3)
            available_gb = virtual_mem.get("available", 0) / (1024**3)

            memory_table.add_row("Total", f"{total_gb:.2f} GB")
            memory_table.add_row("Used", f"{used_gb:.2f} GB")
            memory_table.add_row("Available", f"{available_gb:.2f} GB")

            color = "green"
            if memory_percent > 80:
                color = "red"
            elif memory_percent > 50:
                color = "yellow"

            memory_table.add_row("Percent Used", f"[{color}]{memory_percent:.1f}%[/]")

        # Create disk table
        disk_table = Table(show_header=True, header_style="bold magenta")
        disk_table.add_column("Mount")
        disk_table.add_column("Used")
        disk_table.add_column("Total")
        disk_table.add_column("Percent")

        disk_info = sys_metrics.get("disk", {})
        for mount, data in disk_info.items():
            if mount == "io":
                continue

            if isinstance(data, dict) and "total" in data:
                total_gb = data["total"] / (1024**3)
                used_gb = data["used"] / (1024**3)
                percent = data["percent"]

                color = "green"
                if percent > 80:
                    color = "red"
                elif percent > 50:
                    color = "yellow"

                disk_table.add_row(
                    mount, f"{used_gb:.1f} GB", f"{total_gb:.1f} GB", f"[{color}]{percent:.1f}%[/]"
                )

        # Create network table
        network_table = Table(show_header=True, header_style="bold magenta")
        network_table.add_column("Network")
        network_table.add_column("Value")

        net_info = sys_metrics.get("network", {})
        if net_info:
            sent_mb = net_info.get("bytes_sent", 0) / (1024**2)
            recv_mb = net_info.get("bytes_recv", 0) / (1024**2)

            network_table.add_row("Sent", f"{sent_mb:.2f} MB")
            network_table.add_row("Received", f"{recv_mb:.2f} MB")

        # System panel with all tables
        layout["system"].update(
            Panel(
                Layout(
                    Panel(cpu_table, title="CPU", border_style="green"),
                    Panel(memory_table, title="Memory", border_style="blue"),
                    Panel(disk_table, title="Disk", border_style="yellow"),
                    Panel(network_table, title="Network", border_style="magenta"),
                ),
                title="System Metrics",
                border_style="cyan",
            )
        )

        # Create applications panel
        if not app_metrics:
            layout["apps"].update(
                Panel("No applications being monitored", title="Applications", border_style="red")
            )
        else:
            app_table = Table(show_header=True, header_style="bold cyan")
            app_table.add_column("Application")
            app_table.add_column("Status")
            app_table.add_column("Details")

            for name, metrics in app_metrics.items():
                status = metrics.get("status", "unknown")

                status_color = "green"
                if status in ["error", "not_running"]:
                    status_color = "red"
                elif status in ["unhealthy", "inactive"]:
                    status_color = "yellow"

                # Format details
                details = ""
                if "error" in metrics:
                    details = metrics["error"]

                elif "process" in metrics:
                    proc = metrics["process"]
                    details = f"PID: {proc.get('pid', 'N/A')}, CPU: {proc.get('cpu_percent', 0):.1f}%, Memory: {proc.get('memory_percent', 0):.1f}%"

                elif "http" in metrics:
                    details = f"HTTP Status: {metrics['http'].get('status_code', 'N/A')}"

                elif "log" in metrics:
                    log = metrics["log"]
                    size_kb = log.get("size", 0) // 1024
                    details = f"Log size: {size_kb} KB"

                app_table.add_row(name, f"[{status_color}]{status}[/]", details)

            layout["apps"].update(Panel(app_table, title="Applications", border_style="cyan"))

        return layout
