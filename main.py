import sys
import os
import shutil
import time
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, QVBoxLayout, QWidget, QTextEdit
)
from PyQt5.QtCore import QThread, pyqtSignal


TARGET_FORMAT = ".avi"
SEARCH_DUR = 120 # seconds


class MoveFilesThread(QThread):
    # Signal to notify the main thread
    new_file_moved = pyqtSignal(str)

    def __init__(self, source_dir, target_dir):
        super().__init__()
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.running = True

    def run(self):
        # Monitor source directory for new TARGET_FORMAT files every SEARCH_DUR secs
        cdate = self.get_current_time()
        self.new_file_moved.emit(f"{cdate}: Started")
        moved_files = set()
        while self.running:
            files = [f for f in os.listdir(self.source_dir) if f.endswith(TARGET_FORMAT)]
            for file_name in files:
                if file_name in moved_files:
                    continue
                
                cdate = self.get_current_time()
                target_name = self.get_target_name(file_name)
                source_path = os.path.join(self.source_dir, file_name)
                target_path = os.path.join(self.target_dir, target_name)

                try:
                    shutil.move(source_path, target_path)
                    moved_files.add(file_name)
                    self.new_file_moved.emit(f"{cdate}: Moved from '$SRC/{file_name}' to '$DST/{target_name}'")
                except Exception as e:
                    print(f"{cdate}: Error moving file '{file_name}': {e}")
                    
            time.sleep(SEARCH_DUR)  # wait 1 minute before checking again

    def stop(self):
        self.running = False
        cdate = self.get_current_time()
        self.new_file_moved.emit(f"{cdate}: Stopped")
        self.wait()
        
    def get_current_time(self):
        return datetime.now().strftime("(%m/%d) %H:%M: ")
    
    def get_target_name(self, file_name):
        target_path = os.path.join(self.target_dir, file_name)
        
        nstack = 0
        while os.path.isfile(target_path):
            target_path = target_path[:-4] + "(%d)"%(nstack) + target_path[-4:]
        
        if nstack > 0:
            target_name = file_name[:-4] + "(%d)"%(nstack) + file_name[-4:]
        else:
            target_name = file_name
        return target_name
        

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Set window properties
        self.setGeometry(800, 400, 400, 400)
        self.setWindowTitle("AVI File Mover")

        # Source and Target directory attributes
        self.source_dir = ""
        self.target_dir = ""
        
        # Layout and Widgets
        layout = QVBoxLayout()
        
        # Buttons and labels
        ## Select source
        self.source_button = QPushButton("Select Source Directory")
        self.source_button.clicked.connect(self.select_source_directory)
        self.source_label = QLabel("Source Directory: Not Selected")
        ## Select target 
        self.target_button = QPushButton("Select Target Directory")
        self.target_button.clicked.connect(self.select_target_directory)
        self.target_label = QLabel("Target Directory: Not Selected")
        ## Toggle start
        self.start_button = QPushButton("Start Move")
        self.start_button.clicked.connect(self.toggle_moving_files)
        self.status_label = QLabel("Status: Idle")
        ## Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)

        # Add widgets to layout
        layout.addWidget(self.source_button)
        layout.addWidget(self.source_label)
        layout.addWidget(self.target_button)
        layout.addWidget(self.target_label)
        layout.addWidget(self.start_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.log_display)
        
        # Set layout to central widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Thread and Timer
        self.file_mover_thread = None

    def select_source_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Source Directory")
        if directory:
            self.source_dir = directory
            self.source_label.setText(f"Source Directory: {directory}")
    
    def select_target_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Target Directory")
        if directory:
            self.target_dir = directory
            self.target_label.setText(f"Target Directory: {directory}")
            
    def toggle_moving_files(self):
        # If file moving is not started, start the process
        if self.file_mover_thread is None or not self.file_mover_thread.isRunning():
            if not self.source_dir or not self.target_dir:
                self.status_label.setText("Error: Please select both directories.")
                return
            
            if self.source_dir == self.target_dir:
                self.status_label.setText("Error: Select different target directory")
                return
            
            # Start moving files in a separate thread
            self.file_mover_thread = MoveFilesThread(self.source_dir, self.target_dir)
            self.file_mover_thread.new_file_moved.connect(self.update_log)
            self.file_mover_thread.start()
            
            # Update button and status label
            self.start_button.setText("Stop Move")
            self.status_label.setText("Status: Moving files...")
            
        # If file moving is already running, stop the process
        else:
            self.file_mover_thread.stop()
            self.file_mover_thread = None  # Reset the thread
            self.start_button.setText("Start Move")
            self.status_label.setText("Status: Stopped")
    
    def update_log(self, message):
        self.log_display.append(message)
        self.log_display.repaint()

    def closeEvent(self, event):
        # Stop the thread when the application closes
        if self.file_mover_thread:
            self.file_mover_thread.stop()
        event.accept()

# Main application execution
app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec_())