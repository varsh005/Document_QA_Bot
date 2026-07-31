from django.contrib import admin
from documents.models import Document, Chunk, ChatSession, ChatMessage


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'file_type', 'status', 'page_or_chunk_count', 'uploaded_at')
    list_filter = ('status', 'file_type')
    search_fields = ('original_filename',)


@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    list_display = ('document', 'order', 'vector_index_position')
    list_filter = ('document',)


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ('role', 'content', 'created_at')


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'created_at')
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('session', 'role', 'created_at')
    list_filter = ('role',)
