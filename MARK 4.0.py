import os
import pandas as pd
import pyautogui
import threading
import time
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QListWidget,
    QTextEdit, QPushButton, QLabel, QFileDialog, QComboBox, QLineEdit,
    QMessageBox, QMenuBar, QAction, QWidget, QCheckBox
)
from PyQt5.QtCore import QPoint, pyqtSignal, Qt
from PyQt5.QtGui import QIcon, QFont
from pynput.mouse import Listener as MouseListener
from pynput.keyboard import Listener as KeyboardListener, Key

# Global variables
actions = []
undo_stack = []
redo_stack = []
counter = 1
recording = False
replaying = False
pause = False
tabela = None
csv_filename = None
time_sleep_value = 0.25  # Default value for time.sleep

translations = {
    'en': {
        'View': 'View',
        'Light Mode': 'Light Mode',
        'Dark Mode': 'Dark Mode',
        'Record': 'Record',
        'Stop': 'Stop',
        'Clear': 'Clear',
        'Replay Actions': 'Replay Actions',
        'Preview Nodes': 'Preview Nodes',
        'Import CSV': 'Import CSV',
        'Export Actions': 'Export Actions',
        'Generate Node Code': 'Generate Node Code',
        'Edit CSV': 'Edit CSV',
        'Repetition Count': 'Repetition Count',
        'Time Sleep Value:': 'Time Sleep Value:',
        'Enable CSV Field Selection': 'Enable CSV Field Selection',
        'Recording... Press "Stop" to finish.': 'Recording... Press "Stop" to finish.',
        'Stop Recording': 'Stop Recording',
        'Recorded actions have been cleared.': 'Recorded actions have been cleared.',
        'Replaying actions...': 'Replaying actions...',
        'Replay completed.': 'Replay completed.',
        'CSV file imported successfully.': 'CSV file imported successfully.',
        'Error importing CSV:': 'Error importing CSV:',
        'No actions recorded to export.': 'No actions recorded to export.',
        'Recorded actions exported successfully to': 'Recorded actions exported successfully to',
        'CSV file opened for editing.': 'CSV file opened for editing.',
        'No CSV file imported.': 'No CSV file imported.',
        'click': 'click',
        'press': 'press',
        'hotkey': 'hotkey',
        'Pause/Resume': 'Pause/Resume',
    },
    'pt': {
        'View': 'Visualizar',
        'Light Mode': 'Modo Claro',
        'Dark Mode': 'Modo Escuro',
        'Record': 'Gravar',
        'Stop': 'Parar',
        'Clear': 'Limpar',
        'Replay Actions': 'Reproduzir Ações',
        'Preview Nodes': 'Pré-visualizar Nós',
        'Import CSV': 'Importar CSV',
        'Export Actions': 'Exportar Ações',
        'Generate Node Code': 'Gerar Código de Nó',
        'Edit CSV': 'Editar CSV',
        'Repetition Count': 'Contagem de Repetições',
        'Time Sleep Value:': 'Valor de Pausa:',
        'Enable CSV Field Selection': 'Habilitar Seleção de Campo CSV',
        'Recording... Pressione "Parar" para finalizar.': 'Gravando... Pressione "Parar" para finalizar.',
        'Stop Recording': 'Parar Gravação',
        'Recorded actions have been cleared.': 'Ações gravadas foram limpas.',
        'Replaying actions...': 'Reproduzindo ações...',
        'Replay completed.': 'Reprodução concluída.',
        'CSV file imported successfully.': 'Arquivo CSV importado com sucesso.',
        'Error importing CSV:': 'Erro ao importar CSV:',
        'No actions recorded to export.': 'Nenhuma ação gravada para exportar.',
        'Recorded actions exported successfully to': 'Ações gravadas exportadas com sucesso para',
        'CSV file opened for editing.': 'Arquivo CSV aberto para edição.',
        'No CSV file imported.': 'Nenhum arquivo CSV importado.',
        'click': 'clique',
        'press': 'pressionar',
        'hotkey': 'atalho',
        'Pause/Resume': 'Pausar/Continuar',
    },
    'ru': {
        'View': 'Просмотр',
        'Light Mode': 'Светлый режим',
        'Dark Mode': 'Темный режим',
        'Record': 'Запись',
        'Stop': 'Остановить',
        'Clear': 'Очистить',
        'Replay Actions': 'Воспроизвести действия',
        'Preview Nodes': 'Предварительный просмотр узлов',
        'Import CSV': 'Импорт CSV',
        'Export Actions': 'Экспорт действий',
        'Generate Node Code': 'Создать код узла',
        'Edit CSV': 'Редактировать CSV',
        'Repetition Count': 'Количество повторений',
        'Time Sleep Value:': 'Время задержки:',
        'Enable CSV Field Selection': 'Включить выбор полей CSV',
        'Recording... Нажмите "Остановить" для завершения.': 'Запись... Нажмите "Остановить" для завершения.',
        'Stop Recording': 'Остановка записи',
        'Recorded actions have been cleared.': 'Записанные действия очищены.',
        'Replaying actions...': 'Воспроизведение действий...',
        'Replay completed.': 'Воспроизведение завершено.',
        'CSV file imported successfully.': 'CSV файл успешно импортирован.',
        'Error importing CSV:': 'Ошибка импорта CSV:',
        'No actions recorded to export.': 'Нет записанных действий для экспорта.',
        'Recorded actions exported successfully to': 'Записанные действия успешно экспортированы в',
        'CSV file opened for editing.': 'CSV файл открыт для редактирования.',
        'No CSV file imported.': 'CSV файл не импортирован.',
        'click': 'щелчок',
        'press': 'нажать',
        'hotkey': 'горячая клавиша',
        'Pause/Resume': 'Пауза/Возобновить',
    }
}

class RecordingOverlay(QWidget):
    start_record_signal = pyqtSignal()
    pause_resume_record_signal = pyqtSignal()
    stop_record_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Recording Overlay")
        self.setGeometry(0, 0, 200, 100)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        layout = QVBoxLayout()
        self.setLayout(layout)
        self.setStyleSheet("background:rgba(0, 0, 0, 128); color:white; font-size:20px;")

        self.label = QLabel(translations['en']['Recording... Press "Stop" to finish.'])
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        control_layout = QHBoxLayout()
        layout.addLayout(control_layout)

        play_button = QPushButton("Play")
        play_button.clicked.connect(self.start_record_signal.emit)
        control_layout.addWidget(play_button)

        pause_button = QPushButton("Pause")
        pause_button.clicked.connect(self.pause_resume_record_signal.emit)
        control_layout.addWidget(pause_button)

        stop_button = QPushButton("Stop")
        stop_button.clicked.connect(self.stop_record_signal.emit)
        control_layout.addWidget(stop_button)

class ActionRecorder(QMainWindow):
    update_preview_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mark: Action Recorder")
        self.setGeometry(100, 100, 1000, 600)
        self.language_code = 'en'
        self.dark_mode = False  # Initial theme is light mode
        self.init_ui()
        self.setWindowIcon(QIcon(r'C:\Users\Enzo\Downloads\iconeidea-removebg-preview.png'))

    def init_ui(self):
        main_layout = QHBoxLayout()  # Main layout

        # Left layout (containing buttons and other widgets)
        left_layout = QVBoxLayout()
        main_layout.addLayout(left_layout)

        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        edit_menu = menubar.addMenu("Edit")
        language_menu = menubar.addMenu("Language")
        view_menu = menubar.addMenu(self.translate("View"))

        # File menu actions
        record_action = QAction("Record", self)
        record_action.triggered.connect(self.start_record)
        file_menu.addAction(record_action)

        stop_action = QAction("Stop", self)
        stop_action.triggered.connect(self.stop_record)
        file_menu.addAction(stop_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu actions
        clear_action = QAction("Clear", self)
        clear_action.triggered.connect(self.clear_actions)
        edit_menu.addAction(clear_action)

        undo_action = QAction("Undo", self)
        undo_action.triggered.connect(self.undo_action)
        edit_menu.addAction(undo_action)

        redo_action = QAction("Redo", self)
        redo_action.triggered.connect(self.redo_action)
        edit_menu.addAction(redo_action)

        # Language menu actions
        english_action = QAction("English", self)
        english_action.triggered.connect(lambda: self.load_translation("en"))
        language_menu.addAction(english_action)

        portuguese_action = QAction("Portuguese", self)
        portuguese_action.triggered.connect(lambda: self.load_translation("pt"))
        language_menu.addAction(portuguese_action)

        russian_action = QAction("Russian", self)
        russian_action.triggered.connect(lambda: self.load_translation("ru"))
        language_menu.addAction(russian_action)

        # View menu actions
        light_mode_action = QAction(self.translate("Light Mode"), self)
        light_mode_action.triggered.connect(lambda: self.change_theme(False))
        view_menu.addAction(light_mode_action)

        dark_mode_action = QAction(self.translate("Dark Mode"), self)
        dark_mode_action.triggered.connect(lambda: self.change_theme(True))
        view_menu.addAction(dark_mode_action)

        # Buttons
        self.replay_button = QPushButton(self.translate('Replay Actions'))
        self.pause_button = QPushButton(self.translate('Preview Nodes'))
        self.import_csv_button = QPushButton(self.translate('Import CSV'))
        self.export_button = QPushButton(self.translate('Export Actions'))
        self.generate_node_code_button = QPushButton(self.translate('Generate Node Code'))
        self.edit_csv_button = QPushButton(self.translate('Edit CSV'))

        # Dropdown for selecting headers
        self.headers_combobox = QComboBox()
        self.headers_combobox.addItems(["Header 1", "Header 2", "Header 3"])

        # Line edit for specifying repetition count
        self.repetition_lineedit = QLineEdit()
        self.repetition_lineedit.setPlaceholderText(self.translate('Repetition Count'))

        # Terminal
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)

        # List widget for displaying nodes
        self.node_list = QListWidget()
        self.node_list.itemSelectionChanged.connect(self.update_code_preview_from_node)

        # Connect buttons to functions
        self.replay_button.clicked.connect(self.start_replay)
        self.pause_button.clicked.connect(self.pause_resume_replay)
        self.import_csv_button.clicked.connect(self.import_csv)
        self.export_button.clicked.connect(self.export_actions)
        self.generate_node_code_button.clicked.connect(self.generate_node_code)
        self.edit_csv_button.clicked.connect(self.edit_csv)

        # Add widgets to left layout
        left_layout.addWidget(self.replay_button)
        left_layout.addWidget(self.pause_button)
        left_layout.addWidget(self.import_csv_button)
        left_layout.addWidget(self.export_button)
        left_layout.addWidget(self.headers_combobox)
        left_layout.addWidget(self.repetition_lineedit)
        left_layout.addWidget(self.generate_node_code_button)
        left_layout.addWidget(self.edit_csv_button)
        left_layout.addWidget(self.terminal)
        left_layout.addWidget(self.node_list)

        # Buttons for recording control
        record_control_layout = QHBoxLayout()
        self.start_record_button = QPushButton(self.translate("Record"))
        self.start_record_button.clicked.connect(self.start_record)
        record_control_layout.addWidget(self.start_record_button)

        self.pause_record_button = QPushButton(self.translate("Pause/Resume"))
        self.pause_record_button.clicked.connect(self.pause_resume_record)
        record_control_layout.addWidget(self.pause_record_button)

        self.stop_record_button = QPushButton(self.translate("Stop"))
        self.stop_record_button.clicked.connect(self.stop_record)
        record_control_layout.addWidget(self.stop_record_button)

        left_layout.addLayout(record_control_layout)

        # Right layout (containing code preview)
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout)

        # QTextEdit for code preview
        self.code_preview = QTextEdit()
        self.code_preview.setReadOnly(False)
        self.code_preview.setPlaceholderText(self.translate('Preview Code (Editable)'))
        self.code_preview.textChanged.connect(self.update_actions_from_code)
        right_layout.addWidget(self.code_preview)

        # Adding interface for CSV field selection
        csv_layout = QVBoxLayout()
        right_layout.addLayout(csv_layout)

        self.csv_field_checkbox = QCheckBox(self.translate('Enable CSV Field Selection'))
        self.csv_field_checkbox.setChecked(False)
        self.csv_field_checkbox.stateChanged.connect(self.enable_csv_field_selection)
        csv_layout.addWidget(self.csv_field_checkbox)

        self.csv_fields_combobox = QComboBox()
        csv_layout.addWidget(self.csv_fields_combobox)

        # Adding time.sleep selector
        time_sleep_layout = QHBoxLayout()
        time_sleep_label = QLabel(self.translate('Time Sleep Value:'))
        self.time_sleep_selector = QLineEdit()
        time_sleep_layout.addWidget(time_sleep_label)
        time_sleep_layout.addWidget(self.time_sleep_selector)
        csv_layout.addLayout(time_sleep_layout)

        # Set main layout as the window layout
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Connect the signal to the slot for updating code preview
        self.update_preview_signal.connect(self.update_preview_code)

        # Initialize recording overlay
        self.overlay = RecordingOverlay(self)
        self.overlay.start_record_signal.connect(self.start_record)
        self.overlay.pause_resume_record_signal.connect(self.pause_resume_record)
        self.overlay.stop_record_signal.connect(self.stop_record)

        # Set initial theme and font
        self.change_theme(self.dark_mode)
        self.set_font()

    def load_translation(self, language_code):
        self.language_code = language_code
        self.update_ui_texts()

    def update_ui_texts(self):
        self.setWindowTitle(self.translate("Mark: Action Recorder"))
        self.replay_button.setText(self.translate('Replay Actions'))
        self.pause_button.setText(self.translate('Preview Nodes'))
        self.import_csv_button.setText(self.translate('Import CSV'))
        self.export_button.setText(self.translate('Export Actions'))
        self.generate_node_code_button.setText(self.translate('Generate Node Code'))
        self.edit_csv_button.setText(self.translate('Edit CSV'))
        self.repetition_lineedit.setPlaceholderText(self.translate('Repetition Count'))
        self.csv_field_checkbox.setText(self.translate('Enable CSV Field Selection'))
        self.code_preview.setPlaceholderText(self.translate('Preview Code (Editable)'))
        self.start_record_button.setText(self.translate('Record'))
        self.pause_record_button.setText(self.translate('Pause/Resume'))
        self.stop_record_button.setText(self.translate('Stop'))
        self.overlay.label.setText(self.translate('Recording... Press "Stop" to finish.'))

    def translate(self, text):
        return translations[self.language_code].get(text, text)

    def enable_csv_field_selection(self, state):
        if state == 2:
            self.csv_fields_combobox.clear()
            if tabela is not None:
                self.csv_fields_combobox.addItems(tabela.columns)

    def start_record(self):
        global recording
        recording = True
        self.showMinimized()
        self.print_terminal(self.translate('Recording... Press "Stop" to finish.'))
        self.overlay.show()
        threading.Thread(target=self.record).start()

    def pause_resume_record(self):
        global pause
        if not pause:
            self.print_terminal(self.translate("Pausing recording..."))
        else:
            self.print_terminal(self.translate("Resuming recording..."))
        pause = not pause

    def record(self):
        with MouseListener(on_click=self.on_click), KeyboardListener(on_press=self.on_press) as listener:
            listener.join()

    def on_click(self, x, y, button, pressed):
        global recording
        if pressed and recording:
            if not self.geometry().contains(self.mapFromGlobal(QPoint(x, y))):
                actions.append(("click", (x, y)))
                self.update_preview_signal.emit()
                self.update_node_list()

    def on_press(self, key):
        global recording
        if recording:
            try:
                if hasattr(key, 'char'):
                    actions.append(("press", key.char))
                elif key in [Key.ctrl, Key.shift, Key.alt]:
                    actions.append(("hotkey", key.name))
                else:
                    if key == Key.space:
                        actions.append(("press", "space"))
                    elif key == Key.backspace:
                        actions.append(("press", "backspace"))
                    elif key == Key.cmd:
                        actions.append(("press", "win"))
                    else:
                        actions.append(("press", key.name))
                self.update_preview_signal.emit()
                self.update_node_list()
            except AttributeError:
                self.print_terminal(self.translate("Error handling key press."))

    def stop_record(self):
        global recording, counter
        recording = False
        self.overlay.hide()
        self.showNormal()
        self.print_terminal(self.translate(f"Node {counter} created."))
        counter += 1
        self.update_node_list()

    def start_replay(self):
        global replaying, recording
        if not recording:
            replaying = True
            self.print_terminal(self.translate("Replaying..."))
            threading.Thread(target=self.replay).start()

    def replay(self):
        global replaying, pause
        pause = False
        self.print_terminal(self.translate("Replaying actions..."))
        for action_type, value in actions:
            if replaying:
                try:
                    if action_type == "click":
                        pyautogui.click(*value)
                        time.sleep(time_sleep_value)
                    elif action_type == "press":
                        pyautogui.press(value)
                        time.sleep(time_sleep_value)
                    elif action_type == "hotkey":
                        pyautogui.hotkey(value)
                        time.sleep(time_sleep_value)
                    while pause:
                        time.sleep(0.1)
                    if not replaying:
                        break
                except Exception as e:
                    self.print_terminal(self.translate(f"Error during replay: {e}"))
                    break
            else:
                break
        self.print_terminal(self.translate("Replay completed."))

    def pause_resume_replay(self):
        global pause
        if not pause:
            self.print_terminal(self.translate("Pausing replay..."))
        else:
            self.print_terminal(self.translate("Resuming replay..."))
        pause = not pause

    def import_csv(self):
        global tabela, csv_filename
        csv_filename, _ = QFileDialog.getOpenFileName(self, self.translate("Import CSV"), "", "CSV Files (*.csv)")
        if csv_filename:
            try:
                tabela = pd.read_csv(csv_filename)
                self.print_terminal(self.translate("CSV file imported successfully."))
                self.headers_combobox.clear()
                self.headers_combobox.addItems(tabela.columns)
            except Exception as e:
                self.print_terminal(self.translate(f"Error importing CSV: {e}"))

    def export_actions(self):
        if not actions:
            self.print_terminal(self.translate("No actions recorded to export."))
            return
        filename, _ = QFileDialog.getSaveFileName(self, self.translate("Export Actions"), "", "Text Files (*.txt)")
        if filename:
            with open(filename, "w", encoding="utf-8") as file:
                for action_type, value in actions:
                    file.write(f"{action_type}: {value}\n")
            self.print_terminal(self.translate(f"Recorded actions exported successfully to '{filename}'."))

    def clear_actions(self):
        global actions, counter
        actions.clear()
        undo_stack.clear()
        redo_stack.clear()
        counter = 1  # Resetting the counter
        self.print_terminal(self.translate("Recorded actions have been cleared."))
        self.update_preview_signal.emit()  # Updating the preview
        self.update_node_list()

    def generate_node_code(self):
        global counter
        repetition_count = self.repetition_lineedit.text()
        if not repetition_count.isdigit():
            self.print_terminal(self.translate("Invalid repetition count."))
            return
        repetition_count = int(repetition_count)

        selected_header = self.headers_combobox.currentText()
        if not selected_header:
            self.print_terminal(self.translate("Please select a header."))
            return

        filename, _ = QFileDialog.getSaveFileName(self, self.translate("Save Node Code"), "", "Python Files (*.py)")
        if filename:
            code = f"import pyautogui\nimport pandas as pd\nimport time\n\npyautogui.PAUSE = 0.3\n"
            if selected_header != "Header 1":
                code += f"tabela = pd.read_csv('{csv_filename}')\n"
            if selected_header == "Header 2":
                code += "for linha in tabela.index:\n"
            elif selected_header == "Header 1":
                code += f"for linha in range({repetition_count}):\n"
            for action_type, value in actions:
                if action_type == "click":
                    x, y = value
                    code += f"\tpyautogui.click({x}, {y})\n"
                    code += f"\ttime.sleep({time_sleep_value})\n"
                elif action_type == "press":
                    code += f"\tpyautogui.press('{value}')\n"
                    code += f"\ttime.sleep({time_sleep_value})\n"
                elif action_type == "hotkey":
                    code += f"\tpyautogui.hotkey('{value}')\n"
                    code += f"\ttime.sleep({time_sleep_value})\n"
            with open(filename, "w", encoding="utf-8") as file:
                file.write(code)
            self.print_terminal(self.translate(f"Node code generated successfully in '{filename}'!"))
            counter += 1
            self.update_node_list()

    def print_terminal(self, text):
        self.terminal.append(text)

    def update_preview_code(self):
        preview_code = ""
        estimated_time = 0  # Estimated execution time
        for action_type, value in actions:
            if action_type == "click":
                preview_code += f"{self.translate('click')} {value}\n"
                estimated_time += time_sleep_value
            elif action_type == "press":
                preview_code += f"{self.translate('press')} {value}\n"
                estimated_time += time_sleep_value
            elif action_type == "hotkey":
                preview_code += f"{self.translate('hotkey')} {value}\n"
                estimated_time += time_sleep_value
        self.code_preview.setPlainText(preview_code)
        self.print_terminal(self.translate(f"Estimated time for execution: {estimated_time:.2f} seconds"))

    def edit_csv(self):
        if not csv_filename:
            self.print_terminal(self.translate("No CSV file imported."))
            return
        os.system(f"start excel {csv_filename}")  # Open the CSV in Excel
        self.print_terminal(self.translate("CSV file opened for editing."))

    def update_actions_from_code(self):
        global actions
        actions.clear()
        for line in self.code_preview.toPlainText().split('\n'):
            if line:
                parts = line.split(' ')
                action_type = parts[0]
                value = ' '.join(parts[1:])
                if action_type == self.translate("click"):
                    x, y = value.strip("()").split(', ')
                    actions.append(("click", (int(x), int(y))))
                elif action_type == self.translate("press"):
                    actions.append(("press", value.strip()))
                elif action_type == self.translate("hotkey"):
                    actions.append(("hotkey", value.strip()))
        self.print_terminal(self.translate("Actions updated from code."))
        self.update_node_list()

    def update_node_list(self):
        self.node_list.clear()
        for i, (action_type, value) in enumerate(actions):
            self.node_list.addItem(f"Node {i + 1}: {action_type} {value}")

    def update_code_preview_from_node(self):
        selected_items = self.node_list.selectedItems()
        if not selected_items:
            return
        selected_text = selected_items[0].text()
        node_number = int(selected_text.split(' ')[1].strip(':'))
        self.highlight_node_in_preview(node_number)

    def highlight_node_in_preview(self, node_number):
        preview_text = self.code_preview.toPlainText()
        lines = preview_text.split('\n')
        highlighted_text = ""
        for i, line in enumerate(lines):
            if i == node_number - 1:
                highlighted_text += f"# Node {node_number}\n{line}\n"
            else:
                highlighted_text += f"{line}\n"
        self.code_preview.setPlainText(highlighted_text)

    def undo_action(self):
        if actions:
            action = actions.pop()
            undo_stack.append(action)
            self.update_preview_signal.emit()
            self.update_node_list()

    def redo_action(self):
        if undo_stack:
            action = undo_stack.pop()
            actions.append(action)
            self.update_preview_signal.emit()
            self.update_node_list()

    def change_theme(self, dark_mode):
        self.dark_mode = dark_mode
        if self.dark_mode:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #12263b;
                    color: white;
                }
                QLabel, QPushButton, QTextEdit, QListWidget, QComboBox, QLineEdit, QCheckBox {
                    color: white;
                    background-color: #18334e;
                }
                QMenuBar, QMenu, QMenu::item {
                    background-color: #18324e;
                    color: white;
                }
                QMenu::item:selected {
                    background-color: #6397cf;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #e6e6ff;
                    color: black;
                }
                QLabel, QPushButton, QTextEdit, QListWidget, QComboBox, QLineEdit, QCheckBox {
                    color: black;
                    background-color: #eaeffa;
                }
                QMenuBar, QMenu, QMenu::item {
                    background-color: #eaeffa;
                    color: black;
                }
                QMenu::item:selected {
                    background-color: #DDDDDD;
                }
            """)

    def set_font(self):
        font = QFont("Arial", 10, QFont.Bold)
        self.setFont(font)

def main():
    app = QApplication([])
    app.setStyle('Fusion')
    win = ActionRecorder()
    win.show()
    app.exec_()

if __name__ == '__main__':
    main()
