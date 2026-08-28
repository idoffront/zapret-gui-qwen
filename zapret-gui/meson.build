project('zapret-gui', 'python',
  version: '1.0.0',
  license: 'GPL-3.0',
  meson_version: '>= 0.56.0'
)

# Зависимости
python = import('python').find_installation('python3')
gtk4_dep = dependency('gtk4', version: '>= 4.0')
libadwaita_dep = dependency('libadwaita-1', version: '>= 1.0')

# Скрипты
gui_script = find_program('main.py')
launcher_script = find_program('zapret-gui.sh')

# Установка исполняемого файла
install_data('zapret-gui.sh',
  install_dir: get_option('prefix') / 'bin',
  rename: 'zapret-gui'
)

# Desktop файл
install_data('io.github.snowy-fluffy.zapret-gui.desktop',
  install_dir: get_option('prefix') / 'share' / 'applications'
)

# Иконка
install_data('io.github.snowy-fluffy.zapret-gui.svg',
  install_dir: get_option('prefix') / 'share' / 'icons' / 'hicolor' / 'scalable' / 'apps'
)

# PolicyKit правила
install_data('io.github.snowy-fluffy.zapret-gui.policy',
  install_dir: get_option('prefix') / 'share' / 'polkit-1' / 'actions'
)

# Конфигурация по умолчанию (опционально)
install_data('zapret_commands.json',
  install_dir: get_option('prefix') / 'share' / 'zapret-gui',
  rename: 'config.default.json'
)

# Сообщение при установке
message('Zapret Manager готов к установке')
message('Запустите: sudo meson install -C builddir')
