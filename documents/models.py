import uuid
from django.db import models


def upload_path(instance, filename):
    return f"uploads/{instance.id}/{filename}"


class Document(models.Model):
    """A single uploaded PDF or DOCX file."""

    class FileType(models.TextChoices):
        PDF = 'pdf', 'PDF'
        DOCX = 'docx', 'DOCX'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        READY = 'ready', 'Ready'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to=upload_path)
    original_filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FileType.choices)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, default='')

    page_or_chunk_count = models.PositiveIntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.original_filename


class Chunk(models.Model):
    """A single retrievable slice of text from a Document, plus its embedding."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    order = models.PositiveIntegerField()
    text = models.TextField()
    # Position of this chunk's vector inside the document's FAISS index.
    vector_index_position = models.PositiveIntegerField()

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.document.original_filename} · chunk {self.order}"


class ChatSession(models.Model):
    """A conversation scoped to one document."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='sessions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']


class ChatMessage(models.Model):
    """A single turn in a chat session: either the user's question or the bot's answer."""

    class Role(models.TextChoices):
        USER = 'user', 'User'
        ASSISTANT = 'assistant', 'Assistant'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=Role.choices)
    content = models.TextField()
    # For assistant messages: which chunks were used to ground the answer.
    source_chunks = models.ManyToManyField(Chunk, blank=True, related_name='cited_in_messages')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
