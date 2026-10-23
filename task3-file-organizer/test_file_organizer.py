from pathlib import Path

import pytest

import file_organizer as fo


def make(folder: Path, name: str, content: str = "x") -> Path:
    path = folder / name
    path.write_text(content, encoding="utf-8")
    return path


def snapshot(folder: Path):
    return sorted(str(p.relative_to(folder)) for p in folder.rglob("*"))


def test_sorts_by_extension(tmp_path):
    make(tmp_path, "a.txt", "A")
    make(tmp_path, "b.pdf", "B")
    make(tmp_path, "c.PNG", "C")
    fo.organize(tmp_path)
    assert (tmp_path / "txt" / "a.txt").read_text() == "A"
    assert (tmp_path / "pdf" / "b.pdf").read_text() == "B"
    assert (tmp_path / "png" / "c.PNG").read_text() == "C"
    assert not (tmp_path / "a.txt").exists()


def test_no_extension_and_multi_dot(tmp_path):
    make(tmp_path, "README")
    make(tmp_path, "archive.tar.gz")
    fo.organize(tmp_path)
    assert (tmp_path / "no_extension" / "README").exists()
    assert (tmp_path / "gz" / "archive.tar.gz").exists()


def test_never_overwrites_existing_file(tmp_path):
    (tmp_path / "txt").mkdir()
    make(tmp_path / "txt", "a.txt", "OLD")
    make(tmp_path, "a.txt", "NEW")
    results = fo.organize(tmp_path)
    assert (tmp_path / "txt" / "a.txt").read_text() == "OLD"
    assert (tmp_path / "txt" / "a (1).txt").read_text() == "NEW"
    assert results[0].renamed is True


def test_rename_counter_keeps_increasing(tmp_path):
    (tmp_path / "txt").mkdir()
    make(tmp_path / "txt", "a.txt", "1")
    make(tmp_path / "txt", "a (1).txt", "2")
    make(tmp_path, "a.txt", "3")
    fo.organize(tmp_path)
    assert (tmp_path / "txt" / "a (2).txt").read_text() == "3"
    assert (tmp_path / "txt" / "a.txt").read_text() == "1"
    assert (tmp_path / "txt" / "a (1).txt").read_text() == "2"


def test_renamed_name_colliding_with_incoming_file(tmp_path):
    """'a.txt' gets renamed to 'a (1).txt' while 'a (1).txt' is also arriving."""
    (tmp_path / "txt").mkdir()
    make(tmp_path / "txt", "a.txt", "OLD")
    make(tmp_path, "a.txt", "N1")
    make(tmp_path, "a (1).txt", "N2")
    fo.organize(tmp_path)
    contents = sorted(p.read_text() for p in (tmp_path / "txt").iterdir())
    assert contents == ["N1", "N2", "OLD"]  # nothing lost


def test_dry_run_changes_nothing_and_matches_real_run(tmp_path):
    def build(root: Path) -> None:
        root.mkdir()
        (root / "txt").mkdir()
        make(root / "txt", "a.txt", "OLD")
        make(root, "a.txt", "N1")
        make(root, "a (1).txt", "N2")
        make(root, "b.pdf")

    dry_dir, real_dir = tmp_path / "dry", tmp_path / "real"
    build(dry_dir)
    build(real_dir)
    before = snapshot(dry_dir)

    dry = fo.organize(dry_dir, dry_run=True)
    assert snapshot(dry_dir) == before
    assert all(r.status == "would-move" for r in dry)

    real = fo.organize(real_dir)
    assert [str(r.destination.relative_to(dry_dir)) for r in dry] == [
        str(r.destination.relative_to(real_dir)) for r in real
    ]


def test_empty_directory(tmp_path):
    assert fo.organize(tmp_path) == []
    assert snapshot(tmp_path) == []


def test_missing_and_invalid_target(tmp_path):
    with pytest.raises(FileNotFoundError):
        fo.organize(tmp_path / "nope")
    file_path = make(tmp_path, "f.txt")
    with pytest.raises(NotADirectoryError):
        fo.organize(file_path)


def test_hidden_files_and_subfolders_untouched(tmp_path):
    make(tmp_path, ".secret.txt")
    (tmp_path / "docs").mkdir()
    make(tmp_path / "docs", "inner.txt")
    results = fo.organize(tmp_path)
    assert (tmp_path / ".secret.txt").exists()
    assert (tmp_path / "docs" / "inner.txt").exists()
    assert [r.status for r in results] == ["skipped"]


def test_symlinks_are_skipped(tmp_path):
    real = make(tmp_path, "real.txt")
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(real)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not supported here")
    fo.organize(tmp_path)
    assert link.is_symlink()


def test_skip_list_protects_log_file(tmp_path):
    log = make(tmp_path, "file_organizer.log", "log")
    fo.organize(tmp_path, skip=[log])
    assert log.exists()


def test_permission_error_does_not_stop_the_run(tmp_path, monkeypatch):
    make(tmp_path, "a.txt", "A")
    make(tmp_path, "b.txt", "B")
    real_move = fo.shutil.move

    def flaky_move(src, dst, *args, **kwargs):
        if Path(src).name == "a.txt":
            raise PermissionError("denied")
        return real_move(src, dst, *args, **kwargs)

    monkeypatch.setattr(fo.shutil, "move", flaky_move)
    results = {r.source.name: r for r in fo.organize(tmp_path)}

    assert results["a.txt"].status == "error"
    assert "permission denied" in results["a.txt"].message
    assert (tmp_path / "a.txt").read_text() == "A"        # source untouched
    assert not (tmp_path / "txt" / "a.txt").exists()      # no empty placeholder left
    assert (tmp_path / "txt" / "b.txt").read_text() == "B"  # other file still moved


def test_folder_name_blocked_by_a_file(tmp_path):
    blocker = make(tmp_path, "md", "I am a file")  # same name as the 'md' folder
    make(tmp_path, "notes.md")
    results = {r.source.name: r for r in fo.organize(tmp_path, skip=[blocker])}
    assert results["notes.md"].status == "error"
    assert blocker.read_text() == "I am a file"
    assert (tmp_path / "notes.md").exists()


def test_main_exit_codes_and_log_file(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    make(target, "a.txt")
    log = tmp_path / "run.log"

    assert fo.main([str(target), "--dry-run", "--log-file", str(log)]) == 0
    assert (target / "a.txt").exists()
    assert "DRY-RUN" in log.read_text(encoding="utf-8")

    assert fo.main([str(target), "--log-file", str(log)]) == 0
    assert (target / "txt" / "a.txt").exists()

    assert fo.main([str(tmp_path / "missing"), "--log-file", str(log)]) == 2
