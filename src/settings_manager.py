# src/settings_manager.py
import json
import os
import sys
from typing import Any, Dict, Optional


class SettingsManager:
    """
    Менеджер настроек редактора YAML.
    Сохраняет и загружает настройки в формате JSON.
    """
    SETTINGS_FILENAME = "settings.json"

    def __init__(self):
        # Определяем путь к файлу настроек
        if getattr(sys, 'frozen', False):
            # Режим PyInstaller EXE
            base_path = os.path.dirname(sys.executable)
        else:
            # Режим разработки
            base_path = os.path.dirname(os.path.abspath(__file__))

        self.settings_file_path = os.path.join(base_path, self.SETTINGS_FILENAME)
        self.settings = self._load_default_settings()
        self.load_settings()

    def _load_default_settings(self) -> Dict[str, Any]:
        """Загружает настройки по умолчанию из файла default_settings.json."""
        default_settings_path = self._get_resource_path('default_settings.json')

        if os.path.exists(default_settings_path):
            try:
                with open(default_settings_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"Ошибка загрузки default_settings.json: {e}")

        # Возвращаем настройки по умолчанию, если файл не найден или ошибка
        return {
            # Настройки частиц при печатании
            "typing_particles_enabled": True,

            # Другие потенциальные настройки редактора
            "auto_save_enabled": True,
            "auto_save_interval": 30,  # в секундах
            "show_line_numbers": True,
            "highlight_current_line": True,
            "theme": "dark",
            "font_size": 14,
            "font_family": "Consolas"
        }

    def _get_resource_path(self, relative_path: str) -> str:
        """
        Gets the path to a resource.
        In EXE mode, the file structure is based on PyInstaller --add-data specification.
        """
        if getattr(sys, 'frozen', False):
            # In PyInstaller (EXE) mode
            base_path = os.path.dirname(sys.executable)

            # Check in executable directory (where --add-data puts files)
            full_path = os.path.join(base_path, relative_path)
            if os.path.exists(full_path):
                return full_path

            # Check in PyInstaller temp directory
            try:
                temp_path = sys._MEIPASS
                temp_full_path = os.path.join(temp_path, relative_path)
                if os.path.exists(temp_full_path):
                    return temp_full_path
            except AttributeError:
                # _MEIPASS not available, skip this check
                pass

            # If neither worked, default to base path
            return full_path
        else:
            # In development mode: files are next to this file
            base_path = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(base_path, relative_path)

    def load_settings(self) -> bool:
        """
        Загружает настройки из JSON файла.
        Возвращает True, если загрузка прошла успешно.
        """
        if not os.path.exists(self.settings_file_path):
            # Если файла нет, используем настройки по умолчанию
            self.save_settings()
            return False

        try:
            with open(self.settings_file_path, 'r', encoding='utf-8') as f:
                loaded_settings = json.load(f)

            # Обновляем настройки, используя значения по умолчанию для отсутствующих ключей
            default_settings = self._load_default_settings()
            for key, value in default_settings.items():
                if key not in loaded_settings:
                    loaded_settings[key] = value

            self.settings = loaded_settings
            return True
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Ошибка загрузки настроек: {e}")
            # В случае ошибки возвращаемся к настройкам по умолчанию
            self.settings = self._load_default_settings()
            return False

    def save_settings(self) -> bool:
        """
        Сохраняет настройки в JSON файл.
        Возвращает True, если сохранение прошло успешно.
        """
        try:
            # Создаем директорию, если она не существует
            settings_dir = os.path.dirname(self.settings_file_path)
            if settings_dir and not os.path.exists(settings_dir):
                os.makedirs(settings_dir)

            with open(self.settings_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")
            return False

    def get_setting(self, key: str, default_value: Any = None) -> Any:
        """
        Возвращает значение настройки по ключу.
        Если настройка не найдена, возвращает default_value.
        """
        return self.settings.get(key, default_value)

    def set_setting(self, key: str, value: Any) -> None:
        """
        Устанавливает значение настройки по ключу.
        """
        self.settings[key] = value

    def update_settings(self, new_settings: Dict[str, Any]) -> bool:
        """
        Обновляет несколько настроек за раз.
        """
        try:
            self.settings.update(new_settings)
            return self.save_settings()
        except Exception as e:
            print(f"Ошибка обновления настроек: {e}")
            return False

    def reset_to_defaults(self) -> bool:
        """
        Сбрасывает все настройки к значениям по умолчанию.
        """
        self.settings = self._load_default_settings()
        return self.save_settings()

    @property
    def typing_particles_enabled(self) -> bool:
        """Возвращает состояние включения частиц при печатании."""
        return self.get_setting("typing_particles_enabled", True)

    @typing_particles_enabled.setter
    def typing_particles_enabled(self, value: bool) -> None:
        """Устанавливает состояние включения частиц при печатании."""
        self.set_setting("typing_particles_enabled", value)
        self.save_settings()

    @property
    def auto_save_enabled(self) -> bool:
        """Возвращает состояние автосохранения."""
        return self.get_setting("auto_save_enabled", True)

    @auto_save_enabled.setter
    def auto_save_enabled(self, value: bool) -> None:
        """Устанавливает состояние автосохранения."""
        self.set_setting("auto_save_enabled", value)
        self.save_settings()

    @property
    def auto_save_interval(self) -> int:
        """Возвращает интервал автосохранения в секундах."""
        return self.get_setting("auto_save_interval", 30)

    @auto_save_interval.setter
    def auto_save_interval(self, value: int) -> None:
        """Устанавливает интервал автосохранения в секундах."""
        self.set_setting("auto_save_interval", value)
        self.save_settings()

    @property
    def show_line_numbers(self) -> bool:
        """Возвращает состояние отображения номеров строк."""
        return self.get_setting("show_line_numbers", True)

    @show_line_numbers.setter
    def show_line_numbers(self, value: bool) -> None:
        """Устанавливает состояние отображения номеров строк."""
        self.set_setting("show_line_numbers", value)
        self.save_settings()

    @property
    def highlight_current_line(self) -> bool:
        """Возвращает состояние подсветки текущей строки."""
        return self.get_setting("highlight_current_line", True)

    @highlight_current_line.setter
    def highlight_current_line(self, value: bool) -> None:
        """Устанавливает состояние подсветки текущей строки."""
        self.set_setting("highlight_current_line", value)
        self.save_settings()

    @property
    def theme(self) -> str:
        """Возвращает текущую тему."""
        return self.get_setting("theme", "dark")

    @theme.setter
    def theme(self, value: str) -> None:
        """Устанавливает текущую тему."""
        self.set_setting("theme", value)
        self.save_settings()

    @property
    def font_size(self) -> int:
        """Возвращает размер шрифта."""
        size = self.get_setting("font_size", 14)
        # Clamp the value to the acceptable range to ensure consistency
        return max(10, min(24, size))

    @font_size.setter
    def font_size(self, value: int) -> None:
        """Устанавливает размер шрифта."""
        # Ограничиваем размер шрифта в допустимом диапазоне
        clamped_value = max(10, min(24, value))
        self.set_setting("font_size", clamped_value)
        self.save_settings()

    @property
    def font_family(self) -> str:
        """Возвращает семейство шрифтов."""
        return self.get_setting("font_family", "Consolas")

    @font_family.setter
    def font_family(self, value: str) -> None:
        """Устанавливает семейство шрифтов."""
        self.set_setting("font_family", value)
        self.save_settings()