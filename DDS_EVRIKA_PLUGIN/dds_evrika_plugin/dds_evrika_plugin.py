import os
import json
import hashlib
import shutil
import subprocess
from krita import *
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
    QLineEdit,
    QFormLayout,
    QWidget,
    QMessageBox,
    QHBoxLayout,
    QFileDialog
)
from PyQt5.QtCore import QLocale
from sys import platform

# Version 1.1

# Обновляем путь для хранения конфигурации рядом с Krita
PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(PLUGIN_DIR, "settings.json")


# Чтение и запись в JSON файл
class SettingsManager:
    def __init__(self):
        self._settings = {}
        if not os.path.exists(PLUGIN_DIR):
            os.makedirs(PLUGIN_DIR)
        self._load_settings()

    def _load_settings(self):
        """Загружаем настройки из JSON файла."""
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                self._settings = json.load(f)
        else:
            self._settings = {}

    def save_settings(self):
        """Сохранение настроек в JSON файл."""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self._settings, f, indent=4)

    def get(self, key, default=None):
        """Получить значение настройки по ключу."""
        return self._settings.get(key, default)

    def set(self, key, value):
        """Установить или изменить значение настройки."""
        self._settings[key] = value
        self.save_settings()


class EvrikaSettingsWidget(QWidget):
    def __init__(self, settings_manager):
        super().__init__()
        self.settings = settings_manager
        locale = QLocale.system()
        lang = locale.name()

        if lang.startswith("ru"):
            self.locale_ru()
        else:
            self.locale_en()

        # Основной layout
        layout = QVBoxLayout(self)

        # Секция для временных имен файлов
        self.temp_export_check = QCheckBox(self.translations["use_original_export_name"])
        self.temp_import_check = QCheckBox(self.translations["use_original_import_name"])
        self.export_name_input = QLineEdit()
        self.export_name_input.setPlaceholderText(self.translations["export_custom_name"])

        # Загрузка сохраненных настроек
        self.temp_export_check.setChecked(self.settings.get("use_original_export_name", False))
        self.temp_import_check.setChecked(self.settings.get("use_original_import_name", False))
        self.export_name_input.setText(self.settings.get("export_custom_name", ""))

        # Импорт и экспорт: выбор формата и компрессии
        form_layout = QFormLayout()
        self.import_format_combo = QComboBox()
        self.import_format_combo.addItems(["png", "tiff", "bmp", "jpeg", "tga"])
        self.import_format_combo.setCurrentText(self.settings.get("import_format", "png"))

        self.export_compression_combo = QComboBox()
        self.export_compression_combo.addItems(["dxt1", "dxt3", "dxt5", "bc7", "none"])
        self.export_compression_combo.setCurrentText(self.settings.get("export_compression", "dxt1"))

        self.export_mipmap_combo = QComboBox()
        self.export_mipmap_combo.addItems(["1", "2", "3", "4", "5", "Auto"])
        self.export_mipmap_combo.setCurrentText(self.settings.get("export_mipmap", "Auto"))

        # Добавляем поля в форму
        form_layout.addRow(self.translations["import_format"], self.import_format_combo)
        form_layout.addRow(self.translations["export_compression"], self.export_compression_combo)
        form_layout.addRow(self.translations["export_mipmap"], self.export_mipmap_combo)

        # Кнопка "Сохранить"
        save_button = QPushButton(self.translations["save_settings"])
        save_button.clicked.connect(self.save_settings)

        # Добавляем элементы на Layout
        layout.addWidget(QLabel("<b>{}</b>".format(self.translations["temporary_file_settings"])))
        layout.addWidget(self.temp_export_check)
        layout.addWidget(self.temp_import_check)
        layout.addWidget(QLabel(self.translations["custom_export_name"]))
        layout.addWidget(self.export_name_input)
        layout.addLayout(form_layout)
        layout.addWidget(save_button)

    def locale_ru(self):
        self.translations = {
            "use_original_export_name": "Использовать исходное имя при экспорте",
            "use_original_import_name": "Использовать исходное имя при импорте",
            "export_custom_name": "Введите пользовательское название файла для экспорта",
            "import_format": "Формат (импорт)",
            "export_compression": "Компрессия (экспорт)",
            "export_mipmap": "Уровни Mipmap (экспорт)",
            "save_settings": "Сохранить настройки",
            "temporary_file_settings": "Настройки временных файлов",
            "custom_export_name": "Кастомное имя файла для экспорта",
            "saved_seccess_settings": "Настройки успешно сохранены"
        }

    def locale_en(self):
        self.translations = {
            "use_original_export_name": "Use original name when exporting",
            "use_original_import_name": "Use original name when importing",
            "export_custom_name": "Enter custom export file name",
            "import_format": "Format (import)",
            "export_compression": "Compression (export)",
            "export_mipmap": "Mipmap Levels (export)",
            "save_settings": "Save settings",
            "temporary_file_settings": "Temporary file settings",
            "custom_export_name": "Custom export file name",
            "saved_seccess_settings": "Settings saved successfully"
        }

    def save_settings(self):
        """Сохраняем текущие настройки через объект SettingsManager."""
        self.settings.set("use_original_export_name", self.temp_export_check.isChecked())
        self.settings.set("use_original_import_name", self.temp_import_check.isChecked())
        self.settings.set("export_custom_name", self.export_name_input.text())
        self.settings.set("import_format", self.import_format_combo.currentText())
        self.settings.set("export_compression", self.export_compression_combo.currentText())
        self.settings.set("export_mipmap", self.export_mipmap_combo.currentText())
        QMessageBox.information(self, "Evrika Settings", self.translations["saved_seccess_settings"])


class DDSEvrikaPlugin(Extension):

    def __init__(self, parent):
        super().__init__(parent)
        self.settings = SettingsManager()
        self.init_translations()
        
    def setup(self):
        pass

    def init_translations(self):
        locale = QLocale.system()
        lang = locale.name()

        if lang.startswith("ru"):
            self.translations = {
                "import_dds": "Импортировать DDS",
                "import_dds_as": "Импортировать DDS как...",
                "export_dds": "Экспортировать DDS",
                "export_dds_as": "Экспортировать DDS как...",
                "compression_format": "Выберите формат сжатия",
                "use_saved_settings": "Использовать мои настройки",
                "overwrite_settings": "Перезаписать текущие настройки",
                "mipmap_levels": "Уровни Mipmap",
                "ok": "ОК",
                "cancel": "Отмена",
                "error": "Ошибка",
                "error_processing": "Ошибка при обработке файла: ",
                "file_saved": "Файл успешно сохранён в формате DDS: ",
                "no_document": "Нет активного документа для экспорта.",
                "settings": "Настройки Evrika",
                "import_format": "Выберите формат изображения"
            }
        else:
            self.translations = {
                "import_dds": "Import DDS",
                "import_dds_as": "Import DDS as...",
                "export_dds": "Export DDS",
                "export_dds_as": "Export DDS as...",
                "compression_format": "Select compression format",
                "use_saved_settings": "Use my settings",
                "overwrite_settings": "Overwrite current settings",
                "mipmap_levels": "Mipmap levels",
                "ok": "OK",
                "cancel": "Cancel",
                "error": "Error",
                "error_processing": "Error processing file: ",
                "file_saved": "File successfully saved as DDS: ",
                "no_document": "No active document to export.",
                "settings": "Evrika Settings",
                "import_format": "Select image format"
            }

    def createActions(self, window):
        action_import = window.createAction("ER_DDS_IMPORTER", self.translations["import_dds"], "tools/scripts")
        action_import.triggered.connect(self.importDDS)
        
        action_export = window.createAction("ER_DDS_EXPORTER", self.translations["export_dds"], "tools/scripts")
        action_export.triggered.connect(self.exportDDS)

        action_import_as = window.createAction("ER_DDS_IMPORTER_AS", self.translations["import_dds_as"], "tools/scripts")
        action_import_as.triggered.connect(self.importDDSAs)
        
        action_export_as = window.createAction("ER_DDS_EXPORTER_AS", self.translations["export_dds_as"], "tools/scripts")
        action_export_as.triggered.connect(self.exportDDSAs)

        action_settings = window.createAction("EVRIKA_SETTINGS", self.translations["settings"], "tools/scripts")
        action_settings.triggered.connect(self.showSettingsDialog)

    def showSettingsDialog(self):
        dialog = QDialog()
        layout = QVBoxLayout(dialog)
        settings_widget = EvrikaSettingsWidget(self.settings)
        layout.addWidget(settings_widget)
        dialog.setWindowTitle(self.translations["settings"])
        dialog.exec_()

    def generate_temp_filename(self, original_file_path, new_extension=".png", for_export=False):
        use_original_name = self.settings.get("use_original_export_name", False) if for_export else \
                            self.settings.get("use_original_import_name", False)

        if use_original_name:
            if for_export:
                custom_name = self.settings.get("export_custom_name", "")
                if custom_name:
                    return f"{custom_name}{new_extension}"
            return os.path.splitext(os.path.basename(original_file_path))[0] + new_extension
        else:
            original_filename = os.path.basename(original_file_path)
            original_name, _ = os.path.splitext(original_filename)
            sha256_hash = hashlib.sha256(original_name.encode()).hexdigest()
            return f"temp_{original_name}_{sha256_hash[:8]}{new_extension}"

    def importDDS(self):
        input_file = QFileDialog().getOpenFileName(caption=self.translations["import_dds"], filter="DDS files (*.dds)")[0]
        if not input_file:
            return

        # Используем self.settings.get(), а не self.settings.get()
        temp_filename = self.generate_temp_filename(input_file, f".{self.settings.get('import_format', 'png')}")
        temp_directory_location = os.path.join(os.path.dirname(__file__), 'temp_dds_import')
        if not os.path.isdir(temp_directory_location):
            os.makedirs(temp_directory_location)

        output_file = os.path.join(temp_directory_location, temp_filename)
        imagick_path = os.path.join(os.path.dirname(__file__), 'resources', 'magick.exe') if platform == "win32" else 'magick'
        args = [imagick_path, input_file, output_file]

        try:
            subprocess.run(args, check=True)
            new_document = Krita.instance().openDocument(output_file)
            Krita.instance().activeWindow().addView(new_document)
            shutil.rmtree(temp_directory_location)
        except subprocess.CalledProcessError as e:
            self.showError(self.translations["error_processing"] + str(e))

    def importDDSAs(self):
        dialog = QDialog()
        layout = QVBoxLayout(dialog)

        format_label = QLabel(self.translations["import_format"])
        layout.addWidget(format_label)

        format_combo = QComboBox()
        format_combo.addItems(["png", "tiff", "bmp", "jpeg", "tga"])
        layout.addWidget(format_combo)

        buttons_layout = QHBoxLayout()
        confirm_button = QPushButton(self.translations["ok"])
        cancel_button = QPushButton(self.translations["cancel"])
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(confirm_button)
        layout.addLayout(buttons_layout)

        def process_import_as():
            input_file = QFileDialog().getOpenFileName(caption=self.translations["import_dds"], filter="DDS files (*.dds)")[0]
            if not input_file:
                return

            temp_filename = self.generate_temp_filename(input_file, f".{format_combo.currentText()}")
            temp_directory_location = os.path.join(os.path.dirname(__file__), 'temp_dds_import')
            if not os.path.isdir(temp_directory_location):
                os.makedirs(temp_directory_location)

            output_file = os.path.join(temp_directory_location, temp_filename)
            imagick_path = os.path.join(os.path.dirname(__file__), 'resources', 'magick.exe') if platform == "win32" else 'magick'
            args = [imagick_path, input_file, output_file]

            try:
                subprocess.run(args, check=True)
                new_document = Krita.instance().openDocument(output_file)
                Krita.instance().activeWindow().addView(new_document)
                shutil.rmtree(temp_directory_location)
                dialog.accept()  # Закрываем диалог при успешной обработке
            except subprocess.CalledProcessError as e:
                self.showError(self.translations["error_processing"] + str(e))
                dialog.reject()  # Закрываем диалог, если произошла ошибка

        confirm_button.clicked.connect(process_import_as)
        cancel_button.clicked.connect(dialog.reject)
        dialog.exec_()

    def exportDDS(self):
        """Обычный экспорт DDS с использованием сохранённых настроек."""
        self.process_export(is_export_as=False)

    def exportDDSAs(self):
        self.showImportExportDialog(is_import=False)

    def process_export(self, is_export_as):
        doc = Krita.instance().activeDocument()
        if not doc:
            self.showError(self.translations["no_document"])
            return

        save_file, _ = QFileDialog.getSaveFileName(caption=self.translations["export_dds"], filter="DDS files (*.dds)")
        if not save_file:
            return
        if not save_file.lower().endswith(".dds"):
            save_file += ".dds"

        temp_filename = self.generate_temp_filename(doc.fileName(), ".png", for_export=True)
        temp_directory_location = os.path.join(os.path.dirname(__file__), "temp_dds_export")
        if not os.path.isdir(temp_directory_location):
            os.makedirs(temp_directory_location)

        temp_png_file = os.path.join(temp_directory_location, temp_filename)
        doc.saveAs(temp_png_file)

        imagick_path = os.path.join(os.path.dirname(__file__), "resources", "magick.exe") if platform == "win32" else "magick"
        args = [imagick_path, temp_png_file]

        compression_format = self.settings.get("export_compression", "dxt1")
        mipmap_levels = self.settings.get("export_mipmap", "Auto")

        if compression_format != "none":
            args.extend(["-define", f"dds:compression={compression_format.lower()}"])
        if mipmap_levels != "Auto":
            args.extend(["-define", f"dds:mipmaps={mipmap_levels}"])

        args.append(save_file)

        try:
            subprocess.run(args, check=True)
            self.showMessage(self.translations["file_saved"] + save_file)
        except subprocess.CalledProcessError as e:
            self.showError(self.translations["error_processing"] + str(e))
        finally:
            shutil.rmtree(temp_directory_location)

    def showImportExportDialog(self, is_import=True):
        dialog = QDialog()
        layout = QVBoxLayout(dialog)

        compression_label = QLabel(self.translations["compression_format"])
        layout.addWidget(compression_label)

        compression_format = QComboBox()
        compression_format.addItems(["dxt1", "dxt3", "dxt5", "bc7", "none"])
        layout.addWidget(compression_format)

        mipmaps_label = QLabel(self.translations["mipmap_levels"])
        mipmaps_combo = QComboBox()
        mipmaps_combo.addItems(["Auto", "1", "2", "3", "4", "5"])
        layout.addWidget(mipmaps_combo)

        overwrite_checkbox = QCheckBox(self.translations["overwrite_settings"])
        layout.addWidget(overwrite_checkbox)

        buttons_layout = QHBoxLayout()
        confirm_button = QPushButton(self.translations["ok"])
        cancel_button = QPushButton(self.translations["cancel"])
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(confirm_button)
        layout.addLayout(buttons_layout)

        def save_temporary_settings():
            compression = compression_format.currentText()
            mipmaps = mipmaps_combo.currentText()
            overwrite = overwrite_checkbox.isChecked()

            if overwrite:
                self.save_user_preferences(compression, mipmaps)

            if is_import:
                self.process_import_dialog(compression, mipmaps)
            else:
                self.process_export_dialog(compression, mipmaps)
            
            dialog.accept()
            
        confirm_button.clicked.connect(save_temporary_settings)
        cancel_button.clicked.connect(dialog.reject)
        dialog.exec_()

    def process_import_dialog(self, compression_format, mipmap_levels):
        input_file = QFileDialog().getOpenFileName(caption=self.translations["import_dds"], filter="DDS files (*.dds)")[0]
        if not input_file:
            return

        temp_filename = self.generate_temp_filename(input_file, ".png")
        temp_directory_location = os.path.join(os.path.dirname(__file__), 'temp_dds_import')
        if not os.path.isdir(temp_directory_location):
            os.makedirs(temp_directory_location)

        output_file = os.path.join(temp_directory_location, temp_filename)
        imagick_path = os.path.join(os.path.dirname(__file__), 'resources', 'magick.exe') if platform == "win32" else 'magick'
        args = [imagick_path, input_file, output_file]

        if compression_format != "none":
            args.extend(['-define', f'dds:compression={compression_format.lower()}'])
        if mipmap_levels != "Auto":
            args.extend(['-define', f'dds:mipmaps={mipmap_levels}'])

        try:
            subprocess.run(args, check=True)
            new_document = Krita.instance().openDocument(output_file)
            Krita.instance().activeWindow().addView(new_document)
        except subprocess.CalledProcessError as e:
            self.showError(self.translations["error_processing"] + str(e))
        finally:
            shutil.rmtree(temp_directory_location)

    def process_export_dialog(self, compression_format, mipmap_levels):
        doc = Krita.instance().activeDocument()
        if not doc:
            self.showError(self.translations["no_document"])
            return

        save_file, _ = QFileDialog.getSaveFileName(caption=self.translations["export_dds"], filter="DDS files (*.dds)")
        if not save_file:
            return
        if not save_file.lower().endswith(".dds"):
            save_file += ".dds"

        temp_filename = self.generate_temp_filename(doc.fileName(), ".png", for_export=True)
        temp_directory_location = os.path.join(os.path.dirname(__file__), "temp_dds_export")
        if not os.path.isdir(temp_directory_location):
            os.makedirs(temp_directory_location)

        temp_png_file = os.path.join(temp_directory_location, temp_filename)
        doc.saveAs(temp_png_file)

        imagick_path = os.path.join(os.path.dirname(__file__), "resources", "magick.exe") if platform == "win32" else "magick"
        args = [imagick_path, temp_png_file]

        if compression_format != "none":
            args.extend(["-define", f"dds:compression={compression_format.lower()}"])
        if mipmap_levels != "Auto":
            args.extend(["-define", f"dds:mipmaps={mipmap_levels}"])

        args.append(save_file)

        try:
            subprocess.run(args, check=True)
            self.showMessage(self.translations["file_saved"] + save_file)
        except subprocess.CalledProcessError as e:
            self.showError(self.translations["error_processing"] + str(e))
        finally:
            shutil.rmtree(temp_directory_location)

    def save_user_preferences(self, compression, mipmaps):
        self.settings.set("saved_compression", compression)
        self.settings.set("saved_mipmap", mipmaps)

    def showError(self, message):
        messageBox = QMessageBox()
        messageBox.setWindowTitle(self.translations["error"])
        messageBox.setIcon(QMessageBox.Critical)
        messageBox.setText(message)
        messageBox.setStandardButtons(QMessageBox.Close)
        messageBox.exec()

    def showMessage(self, message):
        messageBox = QMessageBox()
        messageBox.setWindowTitle(self.translations["file_saved"])
        messageBox.setIcon(QMessageBox.Information)
        messageBox.setText(message)
        messageBox.setStandardButtons(QMessageBox.Close)
        messageBox.exec()