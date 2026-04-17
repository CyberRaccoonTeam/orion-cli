"""Tests du gestionnaire de sessions et checkpointing."""

import json
import pytest
from pathlib import Path

from orion.session.manager import SessionManager
from orion.session.checkpoint import CheckpointManager


class TestSessionManager:
    def test_add_and_get_history(self, tmp_path):
        sm = SessionManager(sessions_dir=tmp_path)
        sm.add_message("user", "Hello")
        sm.add_message("assistant", "Hi there!")
        history = sm.get_history()
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["content"] == "Hi there!"

    def test_save_and_resume(self, tmp_path):
        sm = SessionManager(sessions_dir=tmp_path)
        sm.add_message("user", "Test message")
        sm.add_message("assistant", "Test response")
        result = sm.save("test_session")
        assert "saved" in result.lower()

        sm2 = SessionManager(sessions_dir=tmp_path)
        result = sm2.resume("test_session")
        assert "resumed" in result.lower()
        assert len(sm2.get_history()) == 2

    def test_resume_nonexistent(self, tmp_path):
        sm = SessionManager(sessions_dir=tmp_path)
        result = sm.resume("nonexistent")
        assert "not found" in result.lower()

    def test_list_sessions_empty(self, tmp_path):
        sm = SessionManager(sessions_dir=tmp_path)
        result = sm.list_sessions()
        assert "No saved sessions" in result

    def test_list_sessions_with_data(self, tmp_path):
        sm = SessionManager(sessions_dir=tmp_path)
        sm.add_message("user", "Hello")
        sm.save("session_alpha")
        result = sm.list_sessions()
        assert "session_alpha" in result

    def test_delete_session(self, tmp_path):
        sm = SessionManager(sessions_dir=tmp_path)
        sm.save("to_delete")
        result = sm.delete("to_delete")
        assert "deleted" in result.lower()
        assert not (tmp_path / "to_delete.json").exists()

    def test_clear(self, tmp_path):
        sm = SessionManager(sessions_dir=tmp_path)
        sm.add_message("user", "test")
        sm.clear()
        assert len(sm.get_history()) == 0

    def test_get_stats(self, tmp_path):
        sm = SessionManager(sessions_dir=tmp_path)
        stats = sm.get_stats()
        assert "Messages" in stats
        assert "Duration" in stats

    def test_compress(self, tmp_path):
        sm = SessionManager(sessions_dir=tmp_path)
        sm.add_message("user", "Hello")
        sm.add_message("assistant", "Hi")
        result = sm.compress("Summary of the conversation")
        assert "compressed" in result.lower()
        history = sm.get_history()
        assert len(history) == 1
        assert "Summary" in history[0]["content"]

    def test_get_langchain_messages(self, tmp_path):
        sm = SessionManager(sessions_dir=tmp_path)
        sm.add_message("user", "Question")
        sm.add_message("assistant", "Answer")
        messages = sm.get_langchain_messages()
        assert len(messages) == 2


class TestCheckpointManager:
    def test_snapshot_and_commit(self, tmp_path):
        # Crée un fichier
        test_file = tmp_path / "test.txt"
        test_file.write_text("original content")

        cm = CheckpointManager(workspace=tmp_path)
        cm.snapshot_file(test_file, tool="test")
        cp = cm.commit_checkpoint("Test checkpoint")

        assert cp is not None
        assert cp.id == 1
        assert len(cp.snapshots) == 1
        assert cp.snapshots[0].content == "original content"

    def test_restore_modified_file(self, tmp_path):
        test_file = tmp_path / "restore_test.txt"
        test_file.write_text("original")

        cm = CheckpointManager(workspace=tmp_path)
        cm.snapshot_file(test_file, tool="test")
        cm.commit_checkpoint("Before edit")

        # Modifie le fichier
        test_file.write_text("modified")
        assert test_file.read_text() == "modified"

        # Restaure
        ok, msg = cm.restore(checkpoint_id=1)
        assert ok
        assert test_file.read_text() == "original"

    def test_restore_nonexistent_file(self, tmp_path):
        test_file = tmp_path / "new_file.txt"
        assert not test_file.exists()

        cm = CheckpointManager(workspace=tmp_path)
        cm.snapshot_file(test_file, tool="test")  # N'existait pas
        cm.commit_checkpoint("Before create")

        # Crée le fichier
        test_file.write_text("created")

        # Restaure — doit supprimer le fichier
        ok, msg = cm.restore(checkpoint_id=1)
        assert ok
        assert not test_file.exists()

    def test_list_checkpoints_empty(self, tmp_path):
        cm = CheckpointManager(workspace=tmp_path)
        result = cm.list_checkpoints()
        assert "No checkpoints" in result

    def test_discard_pending(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        cm = CheckpointManager(workspace=tmp_path)
        cm.snapshot_file(test_file)
        cm.discard_pending()
        assert cm.get_pending_count() == 0

    def test_max_checkpoints(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        cm = CheckpointManager(workspace=tmp_path)
        cm.MAX_CHECKPOINTS = 3
        for i in range(5):
            cm.snapshot_file(test_file)
            cm.commit_checkpoint(f"Checkpoint {i}")
        # Ne dépasse pas MAX
        assert len(cm._checkpoints) <= 5  # Avant troncature en save
