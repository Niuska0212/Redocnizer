# ui/history_manager.py
"""Sistema de Undo/Redo para la edición de datos."""

from copy import deepcopy
from typing import Any, List, Dict, Tuple


class ChangeRecord:
    """Registro de un cambio individual."""
    
    def __init__(self, row_idx: int, col_name: str, old_value: Any, new_value: Any):
        self.row_idx = row_idx
        self.col_name = col_name
        self.old_value = old_value
        self.new_value = new_value
    
    def __repr__(self):
        return f"Change(row={self.row_idx}, col={self.col_name}, {self.old_value} → {self.new_value})"


class HistoryManager:
    """Gestor de historial de cambios para implementar Undo/Redo."""
    
    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.undo_stack: List[List[ChangeRecord]] = []  # Lista de listas (cada "transacción")
        self.redo_stack: List[List[ChangeRecord]] = []
    
    def record_change(self, row_idx: int, col_name: str, old_value: Any, new_value: Any):
        """Registra un cambio individual."""
        if old_value == new_value:
            return  # Ignorar cambios sin valor
        
        change = ChangeRecord(row_idx, col_name, old_value, new_value)
        
        # Si el undo_stack está vacío o la última transacción ya se "cerró"
        # crear una nueva transacción
        if not self.undo_stack:
            self.undo_stack.append([change])
        else:
            # Agregar al último grupo de transacciones
            self.undo_stack[-1].append(change)
        
        # Limpiar redo_stack cuando hay nuevo cambio
        self.redo_stack.clear()
        
        # Limitar tamaño del historial
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
    
    def commit_transaction(self):
        """Cierra la transacción actual y prepara para una nueva."""
        if self.undo_stack and self.undo_stack[-1]:
            # Si hay cambios, el siguiente cambio empezará con una nueva transacción
            pass
        # Aquí podría agregarse lógica adicional si es necesario
    
    def undo(self) -> List[ChangeRecord]:
        """Deshace el último cambio/transacción.
        
        Retorna la lista de cambios que se deshicieron para poder revertirlos en la UI.
        """
        if not self.undo_stack:
            return []
        
        changes = self.undo_stack.pop()
        self.redo_stack.append(changes)
        return changes
    
    def redo(self) -> List[ChangeRecord]:
        """Rehace el último cambio deshecho.
        
        Retorna la lista de cambios que se rehicieron.
        """
        if not self.redo_stack:
            return []
        
        changes = self.redo_stack.pop()
        self.undo_stack.append(changes)
        return changes
    
    def can_undo(self) -> bool:
        """Indica si hay cambios para deshacer."""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Indica si hay cambios para rehacer."""
        return len(self.redo_stack) > 0
    
    def get_undo_description(self) -> str:
        """Retorna una descripción del próximo cambio a deshacer."""
        if not self.undo_stack:
            return "Deshacer"
        changes = self.undo_stack[-1]
        if len(changes) == 1:
            c = changes[0]
            return f"Deshacer: {c.col_name}"
        else:
            return f"Deshacer ({len(changes)} cambios)"
    
    def get_redo_description(self) -> str:
        """Retorna una descripción del próximo cambio a rehacer."""
        if not self.redo_stack:
            return "Rehacer"
        changes = self.redo_stack[-1]
        if len(changes) == 1:
            c = changes[0]
            return f"Rehacer: {c.col_name}"
        else:
            return f"Rehacer ({len(changes)} cambios)"
    
    def clear(self):
        """Limpia todo el historial."""
        self.undo_stack.clear()
        self.redo_stack.clear()
