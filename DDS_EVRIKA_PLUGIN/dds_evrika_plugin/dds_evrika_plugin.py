import os
import json
import hashlib
import shutil
import tempfile
import importlib
from krita import Krita, Extension, InfoObject

from . import dds_tools
from . import i18n
from .dds_tools import ToolError

VERSION = "1.3.0"


def _krita_major_version():
    try:
        return int(Krita.instance().version().split(".")[0])
    except (ValueError, AttributeError):
        return 5


def _load_qt():
    """Krita 6 is built on Qt6/PyQt6, Krita 5 and older on Qt5/PyQt5."""
    order = ["PyQt6", "PyQt5"] if _krita_major_version() >= 6 else ["PyQt5", "PyQt6"]
    error = None
    for package in order:
        try:
            return (importlib.import_module(package + ".QtWidgets"),
                    importlib.import_module(package + ".QtCore"))
        except ImportError as e:
            error = e
    raise error


QtWidgets, QtCore = _load_qt()
QDialog = QtWidgets.QDialog
QVBoxLayout = QtWidgets.QVBoxLayout
QHBoxLayout = QtWidgets.QHBoxLayout
QFormLayout = QtWidgets.QFormLayout
QGroupBox = QtWidgets.QGroupBox
QLabel = QtWidgets.QLabel
QComboBox = QtWidgets.QComboBox
QPushButton = QtWidgets.QPushButton
QLineEdit = QtWidgets.QLineEdit
QCheckBox = QtWidgets.QCheckBox
QWidget = QtWidgets.QWidget
QMessageBox = QtWidgets.QMessageBox
QFileDialog = QtWidgets.QFileDialog
QLocale = QtCore.QLocale

PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(PLUGIN_DIR, "settings.json")

IMPORT_FORMATS = ["png", "tiff", "bmp", "jpeg", "tga"]


class SettingsManager:
    """Plugin settings stored as JSON next to the plugin."""

    def __init__(self):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                self._settings = json.load(f)
        except (OSError, ValueError):
            self._settings = {}

    def save_settings(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=4)
        except OSError:
            pass

    def get(self, key, default=None):
        return self._settings.get(key, default)

    def set(self, key, value):
        self._settings[key] = value
        self.save_settings()

    def update(self, values):
        self._settings.update(values)
        self.save_settings()

    def export_options(self):
        return {
            "compression": self.get("export_compression", "dxt5"),
            "mipmaps": self.get("export_mipmap", "Auto"),
            "filter_name": self.get("export_filter", "Lanczos"),
            "colorspace": self.get("export_colorspace", dds_tools.COLORSPACE_SRGB),
            "quality": self.get("export_quality", "normal"),
        }

    def save_export_options(self, options):
        self.update({
            "export_compression": options["compression"],
            "export_mipmap": options["mipmaps"],
            "export_filter": options["filter_name"],
            "export_colorspace": options["colorspace"],
            "export_quality": options["quality"],
        })


def _combo(items, current):
    """items: list of (label, value)."""
    combo = QComboBox()
    for label, value in items:
        combo.addItem(label, value)
    index = combo.findData(current)
    if index >= 0:
        combo.setCurrentIndex(index)
    return combo


def _ok_cancel(tr, dialog, ok_text=None):
    layout = QHBoxLayout()
    layout.addStretch(1)
    cancel_button = QPushButton(tr("cancel"))
    ok_button = QPushButton(ok_text or tr("ok"))
    ok_button.setDefault(True)
    cancel_button.clicked.connect(dialog.reject)
    ok_button.clicked.connect(dialog.accept)
    layout.addWidget(cancel_button)
    layout.addWidget(ok_button)
    return layout


class ExportOptionsForm(QFormLayout):
    """Export options shared by the settings dialog and "Export DDS as..."."""

    def __init__(self, tr, options):
        super().__init__()
        self.compression_combo = _combo(
            [(tr("format_" + key), key) for key in dds_tools.COMPRESSION_FORMATS],
            options["compression"])
        self.colorspace_combo = _combo(
            [(tr("colorspace_" + cs), cs) for cs in dds_tools.COLORSPACES], options["colorspace"])
        self.colorspace_combo.setToolTip(tr("colorspace_tooltip"))
        self.mipmap_combo = _combo(
            [(tr("mipmaps_auto"), "Auto"), (tr("mipmaps_none"), "None")] +
            [(tr("mipmaps_count", count=value), value) for value in dds_tools.MIPMAP_CHOICES[2:]],
            options["mipmaps"])
        self.filter_combo = _combo([(f, f) for f in dds_tools.FILTERS], options["filter_name"])
        self.quality_combo = _combo(
            [(tr("quality_" + q), q) for q in dds_tools.QUALITIES], options["quality"])

        self.addRow(tr("compression_format"), self.compression_combo)
        self.addRow(tr("colorspace"), self.colorspace_combo)
        self.addRow(tr("mipmaps"), self.mipmap_combo)
        self.addRow(tr("mipmap_filter"), self.filter_combo)
        self.addRow(tr("quality"), self.quality_combo)

    def options(self):
        return {
            "compression": self.compression_combo.currentData(),
            "mipmaps": self.mipmap_combo.currentData(),
            "filter_name": self.filter_combo.currentData(),
            "colorspace": self.colorspace_combo.currentData(),
            "quality": self.quality_combo.currentData(),
        }


class EvrikaSettingsDialog(QDialog):
    def __init__(self, settings, tr):
        super().__init__()
        self.settings = settings
        self.tr_ = tr
        self.setWindowTitle(tr("action_settings"))
        layout = QVBoxLayout(self)

        # Export
        export_box = QGroupBox(tr("section_export"))
        self.export_form = ExportOptionsForm(tr, settings.export_options())
        self.encoder_combo = _combo(
            [(tr("encoder_" + e), e) for e in dds_tools.ENCODERS],
            settings.get("encoder", dds_tools.ENCODER_AUTO))
        self.export_form.addRow(tr("encoder"), self.encoder_combo)
        export_box.setLayout(self.export_form)
        layout.addWidget(export_box)

        # Import
        import_box = QGroupBox(tr("section_import"))
        import_form = QFormLayout(import_box)
        self.import_format_combo = _combo([(f.upper(), f) for f in IMPORT_FORMATS],
                                          settings.get("import_format", "png"))
        import_form.addRow(tr("import_format"), self.import_format_combo)
        layout.addWidget(import_box)

        # Temporary file names
        names_box = QGroupBox(tr("section_names"))
        names_layout = QVBoxLayout(names_box)
        self.export_name_check = QCheckBox(tr("use_original_export_name"))
        self.export_name_check.setChecked(settings.get("use_original_export_name", False))
        self.import_name_check = QCheckBox(tr("use_original_import_name"))
        self.import_name_check.setChecked(settings.get("use_original_import_name", False))
        self.export_name_input = QLineEdit(settings.get("export_custom_name", ""))
        self.export_name_input.setPlaceholderText(tr("export_custom_name_placeholder"))
        names_layout.addWidget(self.export_name_check)
        names_layout.addWidget(self.import_name_check)
        names_layout.addWidget(QLabel(tr("export_custom_name")))
        names_layout.addWidget(self.export_name_input)
        layout.addWidget(names_box)

        # External tools
        tools_box = QGroupBox(tr("section_tools"))
        tools_form = QFormLayout(tools_box)
        self.magick_input, self.magick_status = self._add_tool_row(
            tools_form, tr("magick_path"), settings.get("magick_path", ""))
        self.cuttlefish_input, self.cuttlefish_status = self._add_tool_row(
            tools_form, tr("cuttlefish_path"), settings.get("cuttlefish_path", ""))
        layout.addWidget(tools_box)
        self.update_tools_status()

        # Interface
        interface_box = QGroupBox(tr("section_interface"))
        interface_form = QFormLayout(interface_box)
        self.language_combo = _combo(
            [(tr("language_auto"), i18n.AUTO)] + [(name, code) for code, name in i18n.available_languages()],
            settings.get("language", i18n.AUTO))
        interface_form.addRow(tr("language"), self.language_combo)
        layout.addWidget(interface_box)

        layout.addLayout(_ok_cancel(tr, self, tr("save")))

    def _add_tool_row(self, form, label, value):
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        line_edit = QLineEdit(value)
        line_edit.setPlaceholderText(self.tr_("path_placeholder"))
        browse = QPushButton(self.tr_("browse"))

        def pick():
            path = QFileDialog.getOpenFileName(self, self.tr_("browse"))[0]
            if path:
                line_edit.setText(path)
                self.update_tools_status()

        browse.clicked.connect(pick)
        line_edit.editingFinished.connect(self.update_tools_status)
        row_layout.addWidget(line_edit)
        row_layout.addWidget(browse)
        status = QLabel()
        status.setWordWrap(True)
        form.addRow(label, row)
        form.addRow("", status)
        return line_edit, status

    def update_tools_status(self):
        for finder, line_edit, status in (
                (dds_tools.find_imagemagick, self.magick_input, self.magick_status),
                (dds_tools.find_cuttlefish, self.cuttlefish_input, self.cuttlefish_status)):
            path = finder(line_edit.text().strip())
            status.setText(self.tr_("tool_found", path=path) if path else self.tr_("tool_not_found"))

    def accept(self):
        language_changed = self.language_combo.currentData() != self.settings.get("language", i18n.AUTO)
        self.settings.update({
            "encoder": self.encoder_combo.currentData(),
            "import_format": self.import_format_combo.currentData(),
            "use_original_export_name": self.export_name_check.isChecked(),
            "use_original_import_name": self.import_name_check.isChecked(),
            "export_custom_name": self.export_name_input.text().strip(),
            "magick_path": self.magick_input.text().strip(),
            "cuttlefish_path": self.cuttlefish_input.text().strip(),
            "language": self.language_combo.currentData(),
        })
        self.settings.save_export_options(self.export_form.options())
        if language_changed:
            QMessageBox.information(self, self.tr_("title_done"), self.tr_("language_restart"))
        super().accept()


class DDSEvrikaPlugin(Extension):

    def __init__(self, parent):
        super().__init__(parent)
        self.settings = SettingsManager()
        self.tr = i18n.Translator(self.settings.get("language", i18n.AUTO),
                                  QLocale.system().uiLanguages())

    def setup(self):
        pass

    def createActions(self, window):
        for action_id, key, handler in (
                ("ER_DDS_IMPORTER", "action_import", self.importDDS),
                ("ER_DDS_IMPORTER_AS", "action_import_as", self.importDDSAs),
                ("ER_DDS_EXPORTER", "action_export", self.exportDDS),
                ("ER_DDS_EXPORTER_AS", "action_export_as", self.exportDDSAs),
                ("EVRIKA_SETTINGS", "action_settings", self.showSettingsDialog)):
            action = window.createAction(action_id, self.tr(key), "tools/scripts")
            action.triggered.connect(handler)

    def showSettingsDialog(self):
        EvrikaSettingsDialog(self.settings, self.tr).exec()

    def generate_temp_filename(self, original_file_path, new_extension=".png", for_export=False):
        use_original_name = self.settings.get("use_original_export_name", False) if for_export else \
                            self.settings.get("use_original_import_name", False)
        original_name = os.path.splitext(os.path.basename(original_file_path))[0] or "untitled"

        if use_original_name:
            if for_export:
                custom_name = self.settings.get("export_custom_name", "")
                if custom_name:
                    return f"{custom_name}{new_extension}"
            return original_name + new_extension
        sha256_hash = hashlib.sha256(original_name.encode()).hexdigest()
        return f"temp_{original_name}_{sha256_hash[:8]}{new_extension}"

    # ----- Import -----

    def importDDS(self):
        self.import_file(self.settings.get("import_format", "png"))

    def importDDSAs(self):
        dialog = QDialog()
        dialog.setWindowTitle(self.tr("action_import_as"))
        layout = QFormLayout(dialog)
        format_combo = _combo([(f.upper(), f) for f in IMPORT_FORMATS],
                              self.settings.get("import_format", "png"))
        layout.addRow(self.tr("import_format"), format_combo)
        layout.addRow(_ok_cancel(self.tr, dialog))
        if dialog.exec():
            self.import_file(format_combo.currentData())

    def import_file(self, image_format):
        input_file = QFileDialog.getOpenFileName(None, self.tr("action_import"),
                                                 self.settings.get("last_import_dir", ""),
                                                 self.tr("file_filter_dds"))[0]
        if not input_file:
            return
        self.settings.set("last_import_dir", os.path.dirname(input_file))

        temp_dir = tempfile.mkdtemp(prefix="evrika_import_")
        try:
            output_file = os.path.join(temp_dir, self.generate_temp_filename(input_file, "." + image_format))
            dds_tools.import_dds(input_file, output_file, self.settings.get("magick_path", ""), temp_dir)
            new_document = Krita.instance().openDocument(output_file)
            if new_document is None:
                self.showError(self.tr("error_open", path=output_file))
                return
            Krita.instance().activeWindow().addView(new_document)
        except ToolError as e:
            self.showError(self.tr.error(e))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # ----- Export -----

    def exportDDS(self):
        """Export with the saved settings."""
        self.export_document(self.settings.export_options())

    def exportDDSAs(self):
        dialog = QDialog()
        dialog.setWindowTitle(self.tr("action_export_as"))
        layout = QVBoxLayout(dialog)
        form = ExportOptionsForm(self.tr, self.settings.export_options())
        layout.addLayout(form)
        remember_checkbox = QCheckBox(self.tr("save_as_default"))
        layout.addWidget(remember_checkbox)
        layout.addLayout(_ok_cancel(self.tr, dialog))
        if not dialog.exec():
            return
        options = form.options()
        if remember_checkbox.isChecked():
            self.settings.save_export_options(options)
        self.export_document(options)

    def export_document(self, options):
        doc = Krita.instance().activeDocument()
        if not doc:
            self.showError(self.tr("no_document"))
            return

        doc_name = os.path.splitext(os.path.basename(doc.fileName()))[0] or doc.name() or "untitled"
        start_dir = self.settings.get("last_export_dir", "") or os.path.dirname(doc.fileName())
        save_file = QFileDialog.getSaveFileName(None, self.tr("action_export"),
                                                os.path.join(start_dir, doc_name + ".dds"),
                                                self.tr("file_filter_dds"))[0]
        if not save_file:
            return
        if not save_file.lower().endswith(".dds"):
            save_file += ".dds"
        self.settings.set("last_export_dir", os.path.dirname(save_file))

        temp_dir = tempfile.mkdtemp(prefix="evrika_export_")
        batchmode = doc.batchmode()
        try:
            temp_png_file = os.path.join(temp_dir, self.generate_temp_filename(doc.fileName(), ".png",
                                                                               for_export=True))
            # exportImage (unlike saveAs) does not rebind the document to the temporary file.
            info = InfoObject()
            info.setProperty("alpha", True)
            info.setProperty("compression", 1)
            info.setProperty("forceSRGB", False)
            info.setProperty("saveSRGBProfile", False)
            doc.setBatchmode(True)
            doc.waitForDone()
            if not doc.exportImage(temp_png_file, info) or not os.path.isfile(temp_png_file):
                self.showError(self.tr("error_temp_export"))
                return

            encoder = dds_tools.export_dds(
                temp_png_file, save_file,
                encoder=self.settings.get("encoder", dds_tools.ENCODER_AUTO),
                magick_path=self.settings.get("magick_path", ""),
                cuttlefish_path=self.settings.get("cuttlefish_path", ""),
                **options)
            self.showMessage(self.tr("export_done", path=save_file,
                                     format=dds_tools.COMPRESSION_FORMATS[options["compression"]][0],
                                     colorspace=self.tr("colorspace_" + options["colorspace"]),
                                     encoder=self.tr("encoder_" + encoder)))
        except ToolError as e:
            self.showError(self.tr.error(e))
        finally:
            doc.setBatchmode(batchmode)
            shutil.rmtree(temp_dir, ignore_errors=True)

    # ----- Messages -----

    def showError(self, message):
        QMessageBox.critical(None, self.tr("title_error"), message)

    def showMessage(self, message):
        QMessageBox.information(None, self.tr("title_done"), message)
