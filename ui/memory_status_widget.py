# ui/memory_status_widget.py
"""
Widget para mostrar estado de memoria y recursos en tiempo real.
"""

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget, QProgressBar
from PySide6.QtCore import Qt
from services.memory_monitor import MemoryMonitor


class MemoryStatusWidget(QWidget):
    """Widget que muestra uso de RAM, CPU y recomendaciones de threads"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        """Inicializa la interfaz"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # Label de estado general
        self.status_label = QLabel("Calculando recursos...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #0b2545;
                font-weight: 600;
                font-size: 12px;
                background-color: #f5f5f5;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #e0e0e0;
            }
        """)
        
        # Barra de RAM
        self.ram_progress = QProgressBar()
        self.ram_progress.setMaximum(100)
        self.ram_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                text-align: center;
                background: #f9f9f9;
                color: #0b2545;
                font-weight: 600;
                font-size: 11px;
                height: 20px;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4caf50,
                    stop:0.7 #ffc107,
                    stop:1 #f44336
                );
                border-radius: 3px;
            }
        """)
        
        # Label de threads recomendados
        self.threads_label = QLabel("Threads óptimos: Calculando...")
        self.threads_label.setStyleSheet("""
            QLabel {
                color: #0b2545;
                font-size: 11px;
                padding: 5px;
            }
        """)
        
        layout.addWidget(QLabel("📊 Estado de Recursos:"))
        layout.addWidget(self.status_label)
        layout.addWidget(QLabel("RAM:"))
        layout.addWidget(self.ram_progress)
        layout.addWidget(self.threads_label)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def update_memory_status(self, status_string: str):
        """
        Actualiza el display con la información de memoria
        
        Args:
            status_string: String formateado de MemoryMonitor.get_status_string()
        """
        self.status_label.setText(status_string)
        
        # Obtener datos y actualizar barra
        report = MemoryMonitor.get_detailed_report()
        percent = report['system_memory']['percent_used']
        threads = report['recommended_threads']
        
        self.ram_progress.setValue(int(percent))
        self.threads_label.setText(
            f"💻 Threads óptimos: {threads} | "
            f"CPU: {report['cpu_percent']:.1f}%"
        )
        
        # Cambiar color de barra según estado
        if percent >= 90:
            color = "#f44336"  # Rojo
        elif percent >= 80:
            color = "#ffc107"  # Naranja
        elif percent >= 70:
            color = "#ff9800"  # Naranja más oscuro
        else:
            color = "#4caf50"  # Verde
        
        self.ram_progress.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                text-align: center;
                background: #f9f9f9;
                color: #0b2545;
                font-weight: 600;
                font-size: 11px;
                height: 20px;
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 3px;
            }}
        """)
