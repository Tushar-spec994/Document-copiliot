"""initial schema with pgvector, full-text search, and RLS

Revision ID: 20261027_0001
Revises:
Create Date: 2026-10-27 00:36:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "20261027_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Create users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # 3. Create source_documents table
    op.create_table(
        "source_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("ticker", sa.String(length=10), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("filing_type", sa.String(length=20), nullable=False, server_default="10-K"),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("filing_date", sa.Date(), nullable=True),
        sa.Column("report_date", sa.Date(), nullable=True),
        sa.Column("accession_number", sa.String(length=32), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_source_documents_ticker", "source_documents", ["ticker"])
    op.create_index("ix_source_documents_fiscal_year", "source_documents", ["fiscal_year"])
    op.create_index(
        "ix_source_documents_accession_number",
        "source_documents",
        ["accession_number"],
        unique=True,
    )

    # 4. Create document_chunks table
    op.create_table(
        "document_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("source_documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("page_number", sa.Integer(), nullable=True),
        sa.Column("section_name", sa.String(length=255), nullable=True),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=True),
        sa.Column("embedding", Vector(768), nullable=True),
        sa.Column(
            "search_vector",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english', chunk_text)", persisted=True),
            nullable=True,
        ),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_document_chunks_document_id", "document_chunks", ["document_id"])
    op.create_index(
        "ix_document_chunks_document_chunk_idx",
        "document_chunks",
        ["document_id", "chunk_index"],
        unique=True,
    )
    # GIN index for full-text search
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_search_vector "
        "ON document_chunks USING gin (search_vector);"
    )
    # HNSW index for cosine distance vector search
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_embedding_hnsw "
        "ON document_chunks USING hnsw (embedding vector_cosine_ops);"
    )

    # 5. Create chat_threads table
    op.create_table(
        "chat_threads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), server_default="New Chat", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_chat_threads_user_id", "chat_threads", ["user_id"])

    # 6. Create chat_messages table
    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "thread_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_threads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("parts", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_chat_messages_thread_id", "chat_messages", ["thread_id"])

    # 7. Create message_citations table
    op.create_table(
        "message_citations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("chat_messages.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "chunk_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("document_chunks.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("citation_index", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("source_passage", sa.Text(), nullable=False),
        sa.Column(
            "metadata_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_message_citations_message_id", "message_citations", ["message_id"])
    op.create_index("ix_message_citations_chunk_id", "message_citations", ["chunk_id"])

    # 8. Row Level Security (RLS) policies
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies WHERE tablename = 'users' AND policyname = 'Users can read own profile'
            ) THEN
                CREATE POLICY "Users can read own profile" ON users
                    FOR SELECT USING (auth.uid() = id);
            END IF;
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies WHERE tablename = 'users' AND policyname = 'Users can update own profile'
            ) THEN
                CREATE POLICY "Users can update own profile" ON users
                    FOR UPDATE USING (auth.uid() = id);
            END IF;
        END $$;
        """
    )

    op.execute("ALTER TABLE source_documents ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies WHERE tablename = 'source_documents' AND policyname = 'Authenticated users can read source documents'
            ) THEN
                CREATE POLICY "Authenticated users can read source documents" ON source_documents
                    FOR SELECT TO authenticated USING (true);
            END IF;
        END $$;
        """
    )

    op.execute("ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies WHERE tablename = 'document_chunks' AND policyname = 'Authenticated users can read document chunks'
            ) THEN
                CREATE POLICY "Authenticated users can read document chunks" ON document_chunks
                    FOR SELECT TO authenticated USING (true);
            END IF;
        END $$;
        """
    )

    op.execute("ALTER TABLE chat_threads ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies WHERE tablename = 'chat_threads' AND policyname = 'Users can manage own threads'
            ) THEN
                CREATE POLICY "Users can manage own threads" ON chat_threads
                    FOR ALL USING (auth.uid() = user_id);
            END IF;
        END $$;
        """
    )

    op.execute("ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies WHERE tablename = 'chat_messages' AND policyname = 'Users can manage messages in own threads'
            ) THEN
                CREATE POLICY "Users can manage messages in own threads" ON chat_messages
                    FOR ALL USING (
                        EXISTS (
                            SELECT 1 FROM chat_threads
                            WHERE chat_threads.id = chat_messages.thread_id
                            AND chat_threads.user_id = auth.uid()
                        )
                    );
            END IF;
        END $$;
        """
    )

    op.execute("ALTER TABLE message_citations ENABLE ROW LEVEL SECURITY;")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_policies WHERE tablename = 'message_citations' AND policyname = 'Users can read citations in own messages'
            ) THEN
                CREATE POLICY "Users can read citations in own messages" ON message_citations
                    FOR SELECT USING (
                        EXISTS (
                            SELECT 1 FROM chat_messages
                            JOIN chat_threads ON chat_threads.id = chat_messages.thread_id
                            WHERE chat_messages.id = message_citations.message_id
                            AND chat_threads.user_id = auth.uid()
                        )
                    );
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    # Drop tables in reverse order of foreign keys
    op.drop_table("message_citations")
    op.drop_table("chat_messages")
    op.drop_table("chat_threads")
    op.drop_table("document_chunks")
    op.drop_table("source_documents")
    op.drop_table("users")
