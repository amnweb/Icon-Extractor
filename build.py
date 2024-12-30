from cx_Freeze import setup, Executable
import datetime
BUILD_VERSION = "1.0.0"
build_options = {
    "silent_level": 1,
    "silent": True,
    "excludes": ['PySide6','pydoc_data','email','tkinter','PySide2'],
    "build_exe": "dist",
    "include_msvcr": False,
    "optimize": 1,
    "include_files": [
            ("app/assets/icon.png","app/assets/icon.png"),
            ("app/assets/icon.ico","app/assets/icon.ico")
        ]
}

directory_table = [
    ("ProgramMenuFolder", "TARGETDIR", "."),
    ("MyProgramMenu", "ProgramMenuFolder", "."),
]

msi_data = {
    "Directory": directory_table,
    "ProgId": [
        ("Prog.Id", None, None, "Icon Extractor for Windows", "IconId", None),
    ],
    "Icon": [
        ("IconId", "app/assets/icon.ico"),
    ],
}

bdist_msi_options = {
    "data": msi_data,
    "install_icon": "app/assets/icon.ico",
    "upgrade_code": "{d8b51da0-15ef-4d07-bdf6-4b022570a9c2}",
    "add_to_path": False,
    "dist_dir": "dist/out",
    "initial_target_dir": r'[LocalAppDataFolder]\Icon Extractor',
    "all_users": False,
    "summary_data": {
        "author": "AmN",
        "comments": "Icon Extractor for Windows",
        "keywords": "windows; icon extractor; windows icon; customization",
    }
}

executables = [
    Executable(
        "main.py",
        base="gui",
        icon="app/assets/icon.ico",
        shortcut_name="Icon Extractor",
        shortcut_dir="MyProgramMenu",
        copyright=f"Copyright (C) {datetime.datetime.now().year} AmN",
        target_name="iex.exe",
    )
]

setup(
    name="iex",
    version=BUILD_VERSION,
    author="AmN",
    description="Icon Extractor for Windows",
    executables=executables,
    options={
        "build_exe": build_options,
        "bdist_msi": bdist_msi_options,
    },
)