# Task 3: Automated File Organizer

A script that scans a folder and sorts the files in it into subfolders based on their extension. **It never overwrites an existing file**: if the name is already taken at the destination, the incoming file is renamed instead.

## Features

- Sorts files into subfolders by extension (`report.pdf` -> `pdf/`, `photo.JPG` -> `jpg/`); files without an extension go to `no_extension/`
- **Never overwrites:** name conflicts get a numbered name (`report.pdf` -> `report (1).pdf` -> `report (2).pdf`). The free name is claimed atomically (exclusive file creation), so even a file that appears at the same moment cannot be replaced
- Prints a clear line for every operation (filename, source, destination)
- Edge cases handled:
  - duplicate filenames (see above)
  - missing permissions: the file is reported as an error, the source stays untouched, no empty leftovers, and the run continues with the next file
  - empty folders: prints "Nothing to organize" and exits cleanly
  - invalid target (missing path, not a folder, filesystem root)
  - hidden files, symbolic links and existing subfolders are left alone
  - a file whose name blocks a would-be folder name is reported, not overwritten
- **Bonus:** logging to a file (with timestamps) in addition to the console
- **Bonus:** `--dry-run` mode previews every change, including renames, without moving anything
- **Bonus (reading ahead):** scheduling with cron / Task Scheduler, see below

Only the Python standard library is used (`os`, `shutil`, `pathlib`, `logging`, `argparse`).

## Project structure

```
task3-file-organizer/
├── file_organizer.py       # the script
├── test_file_organizer.py  # pytest tests
└── README.md
```

## Usage

```bash
# 1. Preview first (nothing is moved)
python file_organizer.py ~/Downloads --dry-run

# 2. Run for real
python file_organizer.py ~/Downloads

# Custom log file location
python file_organizer.py ~/Downloads --log-file ~/organizer.log
```

Example (`pdf/report.pdf` already exists, a new `report.pdf` arrives):

```
Organizing Downloads
[SKIPPED] .hidden: hidden file
[MOVED] Makefile: Downloads/Makefile -> Downloads/no_extension/Makefile
[MOVED] notes.txt: Downloads/notes.txt -> Downloads/txt/notes.txt
[MOVED] photo.JPG: Downloads/photo.JPG -> Downloads/jpg/photo.JPG
[MOVED] report.pdf: Downloads/report.pdf -> Downloads/pdf/report (1).pdf  (renamed: name already existed)
Summary: 4 file(s) moved (1 renamed), 1 skipped, 0 error(s).
```

(The real output prints full absolute paths.)

Exit codes: `0` success, `1` finished but some files had errors, `2` the target folder could not be used.

## Run tests

```bash
pip install pytest
pytest
```

The tests cover sorting, conflict renaming, dry-run accuracy, empty folders, hidden files, permission errors and the CLI exit codes.

## Scheduling (reading ahead)

**Linux / macOS (cron):** run `crontab -e` and add a line to organize Downloads every day at 18:00:

```
0 18 * * * /usr/bin/python3 /home/you/file_organizer.py /home/you/Downloads --log-file /home/you/organizer.log
```

**Windows (Task Scheduler):** from a terminal, create a daily task (use full paths; wrap paths that contain spaces in escaped quotes):

```
schtasks /Create /SC DAILY /ST 18:00 /TN "FileOrganizer" /TR "python C:\Users\You\file_organizer.py C:\Users\You\Downloads --log-file C:\Users\You\organizer.log"
```

Tip: run with `--dry-run` a few times first and check the log before scheduling it.

## Concepts covered

File handling, exception handling, automation, safe file operations, logging, command-line interfaces.
