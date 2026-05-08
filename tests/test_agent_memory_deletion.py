import unittest

from features.agent_memory.service import AgentMemoryRuntime


class FakeOracleAgentMemory:
    def __init__(self) -> None:
        self.deleted_threads: list[str] = []
        self.deleted_users: list[tuple[str, bool]] = []

    def delete_thread(self, thread_id: str) -> int:
        self.deleted_threads.append(thread_id)
        return 1

    def delete_user(self, user_id: str, *, cascade: bool = True) -> int:
        self.deleted_users.append((user_id, cascade))
        return 1


def runtime_with_fake_memory() -> tuple[AgentMemoryRuntime, FakeOracleAgentMemory]:
    runtime = object.__new__(AgentMemoryRuntime)
    fake_memory = FakeOracleAgentMemory()
    runtime._memory = fake_memory
    return runtime, fake_memory


class AgentMemoryDeletionTest(unittest.TestCase):
    def test_delete_thread_removes_current_thread_from_agent_memory(self) -> None:
        runtime, fake_memory = runtime_with_fake_memory()

        deleted = runtime.delete_thread("thread-123")

        self.assertEqual(deleted, 1)
        self.assertEqual(fake_memory.deleted_threads, ["thread-123"])

    def test_delete_thread_rejects_empty_thread_id(self) -> None:
        runtime, fake_memory = runtime_with_fake_memory()

        with self.assertRaisesRegex(ValueError, "thread id"):
            runtime.delete_thread("   ")

        self.assertEqual(fake_memory.deleted_threads, [])

    def test_delete_user_memory_cascades_selected_user_scope(self) -> None:
        runtime, fake_memory = runtime_with_fake_memory()

        deleted = runtime.delete_user_memory("ociopenai")

        self.assertEqual(deleted, 1)
        self.assertEqual(fake_memory.deleted_users, [("ociopenai", True)])

    def test_delete_user_memory_rejects_empty_user_id(self) -> None:
        runtime, fake_memory = runtime_with_fake_memory()

        with self.assertRaisesRegex(ValueError, "user id"):
            runtime.delete_user_memory("")

        self.assertEqual(fake_memory.deleted_users, [])


if __name__ == "__main__":
    unittest.main()
