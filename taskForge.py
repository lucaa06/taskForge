import sys
import sqlite3
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QTreeWidget, QTreeWidgetItem, 
                             QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QComboBox, QLabel)
from PyQt5.QtGui import QColor, QBrush, QFont
from PyQt5.QtCore import Qt, QPropertyAnimation

# Definiamo il dizionario dei colori (le chiavi vengono usate per salvare il valore scelto in DB)
COLOR_DICT = {
    "Rosso": "#FF5733",
    "Verde": "#28B463",
    "Blu": "#3498DB",
    "Giallo": "#F1C40F",
    "Viola": "#8E44AD",
    "Arancione": "#E67E22",
    "Grigio": "#7F8C8D"
}

class taskForge(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initDB()
        self.initUI()
        self.load_data()

    def initDB(self):
        # Creazione/connessione al database "taskForge.db"
        self.conn = sqlite3.connect("taskForge.db")
        c = self.conn.cursor()
        # Tabella delle task: id, titolo e gruppo opzionale
        c.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                group_id INTEGER
            )
        """)
        # Tabella dei gruppi: id, nome e colore (salvato come chiave, ex. "Rosso")
        c.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                color TEXT NOT NULL
            )
        """)
        self.conn.commit()

    def initUI(self):
        self.setWindowTitle("taskForge - Task Manager")
        self.setGeometry(300, 200, 1000, 700)

        # Imposto lo stile globale (tema scuro, bordi arrotondati, linear gradient per i pulsanti)
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QWidget { background-color: #1e1e1e; color: white; font-size: 16px; }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff6600, stop:1 #e65c00);
                border: none;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #e65c00, stop:1 #ff6600);
            }
            QLineEdit, QComboBox, QTreeWidget {
                background-color: #2a2a2a;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        # Widget centrale con layout orizzontale per dividere la finestra in due metà:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        ### Sinistra: Visualizzazione delle task e dei gruppi
        self.left_panel = QWidget()
        left_layout = QVBoxLayout()
        self.left_panel.setLayout(left_layout)
        self.task_tree = QTreeWidget()
        self.task_tree.setHeaderHidden(True)
        self.task_tree.setFont(QFont("Arial", 14))
        left_layout.addWidget(self.task_tree)
        main_layout.addWidget(self.left_panel, stretch=2)

        ### Destra: Comandi per task e gruppi
        self.right_panel = QWidget()
        right_layout = QVBoxLayout()
        self.right_panel.setLayout(right_layout)

        # Sezione Task
        task_cmd_label = QLabel("Task Commands")
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Nuovo task")
        add_task_btn = QPushButton("Aggiungi Task")
        add_task_btn.clicked.connect(self.add_task)
        delete_task_btn = QPushButton("Elimina Task")
        delete_task_btn.clicked.connect(self.delete_task)

        # Sezione Gruppi
        group_cmd_label = QLabel("Group Commands")
        self.group_input = QLineEdit()
        self.group_input.setPlaceholderText("Nuovo gruppo")
        self.color_combo = QComboBox()
        for nome in COLOR_DICT.keys():
            self.color_combo.addItem(nome)
        add_group_btn = QPushButton("Aggiungi Gruppo")
        add_group_btn.clicked.connect(self.add_group)
        delete_group_btn = QPushButton("Elimina Gruppo")
        delete_group_btn.clicked.connect(self.delete_group)

        # Sezione Assegnazione: Assegna task al gruppo
        assign_cmd_label = QLabel("Assegna Task a Gruppo")
        self.assign_combo = QComboBox()
        assign_btn = QPushButton("Assegna")
        assign_btn.clicked.connect(self.assign_task_to_group)

        # Aggiungo i widget al layout dei comandi
        right_layout.addWidget(task_cmd_label)
        right_layout.addWidget(self.task_input)
        right_layout.addWidget(add_task_btn)
        right_layout.addWidget(delete_task_btn)
        right_layout.addSpacing(20)
        right_layout.addWidget(group_cmd_label)
        right_layout.addWidget(self.group_input)
        right_layout.addWidget(self.color_combo)
        right_layout.addWidget(add_group_btn)
        right_layout.addWidget(delete_group_btn)
        right_layout.addSpacing(20)
        right_layout.addWidget(assign_cmd_label)
        right_layout.addWidget(self.assign_combo)
        right_layout.addWidget(assign_btn)
        right_layout.addStretch()  # Spinge gli elementi in alto
        main_layout.addWidget(self.right_panel, stretch=1)

    def update_assign_combo(self):
        """Aggiorna la combo per assegnare il gruppo alle task."""
        self.assign_combo.clear()
        self.assign_combo.addItem("Senza Gruppo", None)
        c = self.conn.cursor()
        c.execute("SELECT id, name FROM groups")
        for group_id, name in c.fetchall():
            self.assign_combo.addItem(name, group_id)

    def load_data(self):
        """Carica i gruppi e le task dal database e li visualizza nel QTreeWidget."""
        self.task_tree.clear()
        c = self.conn.cursor()

        # Elemento speciale per le task senza gruppo
        ungrouped_item = QTreeWidgetItem(self.task_tree)
        ungrouped_item.setText(0, "Senza Gruppo")
        ungrouped_item.setData(0, Qt.UserRole, None)
        ungrouped_item.setBackground(0, QBrush(QColor("#555555")))

        # Carica i gruppi e mappa id -> item
        c.execute("SELECT id, name, color FROM groups")
        group_map = {}
        for group_id, name, color in c.fetchall():
            # Creo un item per il gruppo e setto il colore di sfondo usando la base del colore scelto
            group_item = QTreeWidgetItem(self.task_tree)
            group_item.setText(0, name)
            base_color = QColor(COLOR_DICT.get(color, "#444444"))
            group_item.setBackground(0, QBrush(base_color))
            group_item.setData(0, Qt.UserRole, group_id)
            group_map[group_id] = group_item

        # Carica le task
        c.execute("SELECT id, title, group_id FROM tasks")
        for task_id, title, group_id in c.fetchall():
            if group_id is None or group_id not in group_map:
                parent = ungrouped_item
            else:
                parent = group_map[group_id]
            task_item = QTreeWidgetItem(parent)
            task_item.setText(0, title)
            task_item.setData(0, Qt.UserRole, task_id)

        self.task_tree.expandAll()
        self.update_assign_combo()

        # Applicare un semplice effetto di fade-in
        from PyQt5.QtWidgets import QGraphicsOpacityEffect
        effect = QGraphicsOpacityEffect(self.task_tree)
        self.task_tree.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(500)
        anim.setStartValue(0)
        anim.setEndValue(1)
        anim.start()
        self.anim = anim  # Mantengo il riferimento per evitare il garbage collection

    def add_task(self):
        title = self.task_input.text().strip()
        if title:
            c = self.conn.cursor()
            c.execute("INSERT INTO tasks (title, group_id) VALUES (?, ?)", (title, None))
            self.conn.commit()
            self.task_input.clear()
            self.load_data()

    def delete_task(self):
        item = self.task_tree.currentItem()
        # Verifico che l'item selezionato sia una task (deve avere un parent)
        if item and item.parent() is not None and isinstance(item.data(0, Qt.UserRole), int):
            task_id = item.data(0, Qt.UserRole)
            c = self.conn.cursor()
            c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            self.conn.commit()
            self.load_data()

    def add_group(self):
        name = self.group_input.text().strip()
        if name:
            # Il colore salvato è il nome (es. "Rosso", "Verde", ecc.)
            color = self.color_combo.currentText()
            c = self.conn.cursor()
            c.execute("INSERT INTO groups (name, color) VALUES (?, ?)", (name, color))
            self.conn.commit()
            self.group_input.clear()
            self.load_data()

    def delete_group(self):
        item = self.task_tree.currentItem()
        # Verifico che l'item selezionato rappresenti un gruppo (nessun parent) e NON sia l'item "Senza Gruppo"
        if item and item.parent() is None and item.text(0) != "Senza Gruppo":
            group_id = item.data(0, Qt.UserRole)
            c = self.conn.cursor()
            # Elimino il gruppo e azzero l'assegnazione per le task appartenenti a quel gruppo
            c.execute("DELETE FROM groups WHERE id = ?", (group_id,))
            c.execute("UPDATE tasks SET group_id = NULL WHERE group_id = ?", (group_id,))
            self.conn.commit()
            self.load_data()

    def assign_task_to_group(self):
        item = self.task_tree.currentItem()
        # Assicuriamoci di aver selezionato una task (abbiamo un parent)
        if item and item.parent() is not None and isinstance(item.data(0, Qt.UserRole), int):
            task_id = item.data(0, Qt.UserRole)
            group_id = self.assign_combo.currentData()  # Può essere None
            c = self.conn.cursor()
            c.execute("UPDATE tasks SET group_id = ? WHERE id = ?", (group_id, task_id))
            self.conn.commit()
            self.load_data()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = taskForge()
    window.show()
    sys.exit(app.exec_())
