# CLAUDE.md

## プロジェクト概要

本プロジェクトは、[Model Context Protocol (MCP)](https://modelcontextprotocol.io/quickstart/server) の公式仕様に完全準拠し、Python（FastMCP）を用いて、ClaudeなどのAIエージェントからFirebase（Firestore/FireStorage）に保存されたデータへ安全かつ効率的にアクセスできるMCPサーバーを構築することを目的とします。

---

## 仕様・要件

### 1. 開発方針
- 言語は**Python**を使用
- MCP公式チュートリアル（[Quickstart for Server Developers](https://modelcontextprotocol.io/quickstart/server)）のPython例に準拠
- MCP公式Python SDK（[GitHub](https://github.com/modelcontextprotocol/python-sdk)）を利用
- MCPサーバーの実装には**FastMCP**（[GitHub](https://github.com/jlowin/fastmcp)）を使用
- FastMCPの`transport`プロトコル（stdio/http等）は起動時に選択可能なため、開発時は特に意識せず実装

### 2. ディレクトリ構成例
- MCP公式サーバーサンプル（[sqlite](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/sqlite/src/mcp_server_sqlite)、[git](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/git)）を参考に、
  - `src/`配下にサーバー本体（例：`src/mcp_server_firebase/`）
  - ルートに`main.py`や`Dockerfile`、`requirements.txt`等を配置

### 3. Firestore/FireStorageへのアクセス
- **汎用的なMCPサーバーではなく、アクセス対象のコレクション名やバケット名はソースコード内で固定**
- 必要に応じてアクセス範囲を制限し、セキュリティを担保

### 4. サービスアカウント認証
- Googleサービスアカウントの認証情報（JSONファイル）を**MCPサーバー起動時の引数で指定**し、それを用いてFirebase Admin SDKを初期化
- 例：`python main.py --google-credentials /path/to/service_account.json`

### 5. MCPツール（API）
- Firestore/FireStorageの**コレクション・バケットごと**にツールを分割し、FastMCPの`@mcp.tool()`で実装する。
- 各ツールは「filter条件を指定して検索」できるようにする。
- それぞれのコレクションで持っているカラムと型を下記に列挙し、filterの指定例も記載する。

#### Firestore

##### assetsコレクション
- カラムと型:
  - id: string
  - title: string
  - description: string
  - category: string
  - tags: string[]
  - uploader: string
  - uploadedAt: string (ISO8601日時)
  - updatedAt: string (ISO8601日時)
  - visibility: 'public' | 'private'
  - latestVersionId?: string
- ツール:
  - `search_assets(filter: dict) -> list[dict]`
    - filter例:
      ```json
      { "category": "image", "tags": ["banner"], "visibility": "public", "uploadedAt": ">=2024-06-01" }
      ```
    - サポートする演算子例: `==`, `in`, `array-contains-any`, `>=`, `<=` など

##### versionsコレクション
- カラムと型:
  - id: string
  - assetId: string
  - version: string
  - fileUrl: string
  - fileName: string
  - fileType: string
  - fileSize: number
  - updatedAt: string (ISO8601日時)
  - updatedBy: string
- ツール:
  - `search_versions(filter: dict) -> list[dict]`
    - filter例:
      ```json
      { "assetId": "asset123", "fileType": "image/png", "updatedAt": ">=2024-06-01" }
      ```

##### commentsコレクション
- カラムと型:
  - id: string
  - assetId: string
  - user: string
  - text: string
  - createdAt: string (ISO8601日時)
- ツール:
  - `search_comments(filter: dict) -> list[dict]`
    - filter例:
      ```json
      { "assetId": "asset123", "user": "user456", "createdAt": ">=2024-06-01" }
      ```

#### FireStorage

- バケット名: `owndays-dam.firebasestorage.app`
- ツール:
  - `search_asset_files(filter: dict) -> list[dict]`
    - filter例:
      ```json
      { "prefix": "assets/", "contentType": "image/png", "uploadedAt": ">=2024-06-01" }
      ```
    - サポートするfilterキー例: `prefix`, `contentType`, `uploadedAt` など

- それぞれのツールは、コレクション名やバケット名を関数内で固定し、アクセス範囲を明確に制限する。
- 型ヒント・docstringを丁寧に記述し、AIエージェントがツールの用途を理解しやすいようにする。

### 6. 起動・運用方法
- **Docker化してWebサーバーとして運用**、または**コマンドで標準入出力（stdio）で接続**の両方に対応
- FastMCPの`transport`引数で`http`または`stdio`を選択可能
- サービスアカウント認証情報のパスは起動時引数で渡す

---

## 参考リンク
- [MCP公式チュートリアル（Python）](https://modelcontextprotocol.io/quickstart/server)
- [MCP Python SDK GitHub](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [サーバー構成例（sqlite）](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/sqlite/src/mcp_server_sqlite)
- [サーバー構成例（git）](https://github.com/modelcontextprotocol/servers-archived/tree/main/src/git)
- [Firebase Admin SDK ドキュメント](https://firebase.google.com/docs/admin/setup)

---

## 備考
- Claude for Desktop等のMCPクライアントで利用する場合、[公式ガイド](https://modelcontextprotocol.io/quickstart/server)の設定例に従い、`claude_desktop_config.json`等でMCPサーバーを登録する。
- MCPサーバーのツール定義はPythonの型ヒント・docstringから自動生成されるため、関数定義・コメントを丁寧に記述する。
- コレクション名やバケット名の固定・アクセス範囲制限により、セキュリティを強化する。
- mainスクリプトやDockerfileは両起動方式に対応できるよう設計する。

---

## 今後の拡張例
- Firestore/Storageへの書き込み・更新・削除ツールの追加
- 認証・権限管理の強化
- クエリの柔軟化（複雑な条件検索など） 