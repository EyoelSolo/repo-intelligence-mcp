from pathlib import Path

from app.parser.code_parser import CodeParser


def test_typescript_symbols(tmp_path):

    file = tmp_path / "example.ts"

    file.write_text(
        """
        interface User {
            id: string;
        }

        class UserService {

            getUser(id: string) {
                return id;
            }

        }

        function createUser() {
            return {};
        }
        """,
        encoding="utf-8",
    )

    parser = CodeParser()

    symbols = parser.extract_symbols(
        file,
        "typescript",
    )

    names = {
        symbol.name
        for symbol in symbols
    }

    assert "User" in names
    assert "UserService" in names
    assert "getUser" in names
    assert "createUser" in names