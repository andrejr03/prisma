from __future__ import annotations

from app.retrieval.index import main


def test_index_command_writes_manifest_and_repeats_successfully(tmp_path, capsys):
    index_path = tmp_path / "qdrant"
    manifest_path = tmp_path / "manifest.json"

    first = main(
        [
            "--index-path",
            str(index_path),
            "--manifest-path",
            str(manifest_path),
        ]
    )
    second = main(
        [
            "--index-path",
            str(index_path),
            "--manifest-path",
            str(manifest_path),
        ]
    )

    output = capsys.readouterr().out
    assert first == 0
    assert second == 0
    assert manifest_path.exists()
    assert "index rebuilt" in output
    assert "index up to date" in output
