import subprocess
import os
import shutil
from krita import *
from PyQt5.QtWidgets import (QMessageBox, QFileDialog, QDialog, QWidget, QGridLayout, 
                             QVBoxLayout, QLabel, QComboBox, QPushButton)
from sys import platform

class DDSEvrikaPlugin(Extension):

    def __init__(self, parent):
        super().__init__(parent)
        self.init_translations()  # Initialize language translations

    def setup(self):
        pass

    def init_translations(self):
        """Determine the language based on system locale."""
        locale = QLocale.system()  # Get the system's locale
        lang = locale.name()
        print(f"System locale is: {lang}")

        # Set up translations based on the locale or language
        if lang.startswith("ru"):  # If system's locale is Russian
            self.translations = {
                "import_dds": "Импортировать DDS",
                "export_dds": "Экспортировать в DDS",
                "select_dds_file": "Выберите DDS файл",
                "select_format": "Выберите формат",
                "compression_format": "Выберите формат сжатия",
                "save_as_dds": "Сохранить как DDS",
                "ok": "ОК",
                "cancel": "Отмена",
                "error": "Ошибка",
                "error_processing": "Ошибка при обработке файла: ",
                "file_saved": "Файл успешно сохранен в формате DDS: ",
                "no_document": "Нет активного документа для экспорта.",
            }
        else:  # Default to English
            self.translations = {
                "import_dds": "Import DDS",
                "export_dds": "Export to DDS",
                "select_dds_file": "Select a DDS file",
                "select_format": "Select a format",
                "compression_format": "Select compression format",
                "save_as_dds": "Save as DDS",
                "ok": "OK",
                "cancel": "Cancel",
                "error": "Error",
                "error_processing": "Error processing file: ",
                "file_saved": "File successfully saved as DDS: ",
                "no_document": "No active document to export.",
            }

    def createActions(self, window):
        action_import = window.createAction("ER_DDS_IMPORTER", self.translations["import_dds"], "tools/scripts")
        action_import.triggered.connect(self.importDDS)
        
        action_export = window.createAction("ER_DDS_EXPORTER", self.translations["export_dds"], "tools/scripts")
        action_export.triggered.connect(self.exportDDS)

    def importDDS(self):
        """
        Import DDS file
        """
        input_file = QFileDialog().getOpenFileName(caption=self.translations["select_dds_file"], filter="DDS files (*.dds)")[0]
        if not input_file:
            return

        # Список возможных форматов для импорта
        format_options = ["png", "jpeg", "bmp", "tiff"]

        format_dialog = self.createFormatImportDialog(format_options, self.translations["select_format"])
        if format_dialog.exec_() == QDialog.Accepted:
            selected_format = format_dialog.import_format.currentText()
            temp_directory_location = os.path.join(os.path.dirname(__file__), 'temp_dds')
            if not os.path.isdir(temp_directory_location):
                os.makedirs(temp_directory_location)
            imagick_path = os.path.join(os.path.dirname(__file__), 'resources', 'magick.exe') if platform == "win32" else 'magick'
            output_file = os.path.join(temp_directory_location, os.path.splitext(os.path.basename(input_file))[0] + '.' + selected_format.lower())
            args = [imagick_path, input_file, output_file]
            
            try:
                subprocess.run(args, check=True)
                new_document = Krita.instance().openDocument(output_file)
                Krita.instance().activeWindow().addView(new_document)
            except subprocess.CalledProcessError as e:
                self.showError(self.translations["error_processing"] + str(e))
                shutil.rmtree(temp_directory_location)

            shutil.rmtree(temp_directory_location)

    def exportDDS(self):
        """
        Export document to DDS format with advanced compression options.
        """
        doc = Krita.instance().activeDocument()
        if not doc:
            self.showError(self.translations["no_document"])
            return
        save_file, _ = QFileDialog.getSaveFileName(caption=self.translations["save_as_dds"], filter="DDS files (*.dds)")
        if not save_file:
            return
        if not save_file.lower().endswith('.dds'):
            save_file += ".dds"

        # Предоставляем пользователю выбор формата и параметров сжатия
        format_options = ["png", "tiff", "bmp"]  # Доступные форматы для экспорта (кроме DDS)
        format_dialog = self.createFormatExportDialog(format_options, self.translations["compression_format"])

        if format_dialog.exec_() == QDialog.Accepted:
            selected_format = format_dialog.import_format.currentText()
            compression_format = format_dialog.compression_format.currentText()
            mipmap_levels = format_dialog.mipmaps_combo.currentText()

            temp_directory_location = os.path.join(os.path.dirname(__file__), 'temp_dds_export')
            if not os.path.isdir(temp_directory_location):
                os.makedirs(temp_directory_location)
            
            # Экспорт документа во временный PNG для конвертации через ImageMagick
            temp_png_file = os.path.join(temp_directory_location, "temp_export.png")
            doc.saveAs(temp_png_file)

            # Формируем команду для ImageMagick
            imagick_path = os.path.join(os.path.dirname(__file__), 'resources', 'magick.exe') if platform == "win32" else 'magick'

            # Базовые аргументы
            args = [imagick_path, temp_png_file]

            # Спецификация для сжатия DDS (dxt1, dxt3, dxt5 etc.)
            if compression_format != "none":  # Если выбран формат, отличный от "none"
                args.extend(['-define', f'dds:compression={compression_format.lower()}'])

            # Опция для мип-карт
            if mipmap_levels != "Auto":
                args.extend(['-define', f'dds:mipmaps={mipmap_levels}'])

            # Финальный аргумент: назначение выходного файла
            args.append(save_file)

            # Запуск команды
            try:
                subprocess.run(args, check=True)
                self.showMessage(self.translations["file_saved"] + save_file)
            except subprocess.CalledProcessError as e:
                self.showError(self.translations["error_processing"] + str(e))

            # Очистка временной директории
            shutil.rmtree(temp_directory_location)

    def createFormatImportDialog(self, format_options, title):
        """
        Creates a dialog for selecting formats.
        """
        dialog = QDialog()
        dialog.setWindowTitle(title)
        
        grid = QGridLayout(dialog)
        vbox_left = QVBoxLayout()
        vbox_right = QVBoxLayout()

        format_label = QLabel(self.translations["select_format"])
        vbox_left.addWidget(format_label)
        
        import_format = QComboBox()
        import_format.addItems(format_options)  # Добавляем элементы в выпадающий список
        import_format.setCurrentIndex(0)
        vbox_right.addWidget(import_format)

        confirm_button = QPushButton(self.translations["ok"])
        vbox_right.addWidget(confirm_button)
        
        cancel_button = QPushButton(self.translations["cancel"])
        vbox_left.addWidget(cancel_button)
        
        grid.addLayout(vbox_left, 0, 0)
        grid.addLayout(vbox_right, 0, 1)

        confirm_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        dialog.import_format = import_format

        return dialog

    def createFormatExportDialog(self, format_options, title):
        """
        Creates a dialog for selecting formats and compression settings.
        """
        dialog = QDialog()
        dialog.setWindowTitle(title)

        grid = QGridLayout(dialog)
        vbox_left = QVBoxLayout()
        vbox_right = QVBoxLayout()

        # Метка для выбора формата
        format_label = QLabel(self.translations["select_format"])
        vbox_left.addWidget(format_label)

        # Выпадающий список для выбора формата
        import_format = QComboBox()
        import_format.addItems(format_options)
        import_format.setCurrentIndex(0)
        vbox_right.addWidget(import_format)

        # Метка для выбора сжатия
        compression_label = QLabel(self.translations["compression_format"])
        vbox_left.addWidget(compression_label)

        # Список опций сжатия DDS
        compression_options = ["dxt1", "dxt3", "dxt5", "bc7", "none"]
        compression_format = QComboBox()
        compression_format.addItems(compression_options)  # Выбор формата сжатия
        compression_format.setCurrentIndex(0)
        vbox_right.addWidget(compression_format)

        # Опция для использования мип-карт
        mipmaps_label = QLabel("Mipmap levels")
        vbox_left.addWidget(mipmaps_label)
        
        mipmaps_combo = QComboBox()
        mipmaps_combo.addItems(["Auto", "1", "2", "3", "4", "5"])  # Example mipmap levels
        mipmaps_combo.setCurrentIndex(0)
        vbox_right.addWidget(mipmaps_combo)

        # Кнопки подтверждения и отмены
        confirm_button = QPushButton(self.translations["ok"])
        vbox_right.addWidget(confirm_button)

        cancel_button = QPushButton(self.translations["cancel"])
        vbox_left.addWidget(cancel_button)

        # Добавление layout в диалог
        grid.addLayout(vbox_left, 0, 0)
        grid.addLayout(vbox_right, 0, 1)

        confirm_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        # Передаем данные доступа к выбранным форматам и параметрам
        dialog.import_format = import_format
        dialog.compression_format = compression_format
        dialog.mipmaps_combo = mipmaps_combo

        return dialog

    def showError(self, message):
        """
        Shows an error message dialog.
        """
        messageBox = QMessageBox()
        messageBox.setWindowTitle(self.translations["error"])
        messageBox.setIcon(QMessageBox.Critical)
        messageBox.setText(message)
        messageBox.setStandardButtons(QMessageBox.Close)
        messageBox.exec()

    def showMessage(self, message):
        """
        Shows an information message dialog.
        """
        messageBox = QMessageBox()
        messageBox.setWindowTitle(self.translations["file_saved"])
        messageBox.setIcon(QMessageBox.Information)
        messageBox.setText(message)
        messageBox.setStandardButtons(QMessageBox.Close)
        messageBox.exec()

