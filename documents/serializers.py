from rest_framework import serializers
from documents.models import Document, ChatSession, ChatMessage, Chunk


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = [
            'id', 'original_filename', 'file_type', 'status',
            'error_message', 'page_or_chunk_count', 'uploaded_at',
        ]
        read_only_fields = fields


class ChunkSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chunk
        fields = ['id', 'order', 'text']


class ChatMessageSerializer(serializers.ModelSerializer):
    source_chunks = ChunkSourceSerializer(many=True, read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'role', 'content', 'source_chunks', 'created_at']
        read_only_fields = fields


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ['id', 'document', 'created_at', 'messages']
        read_only_fields = fields
