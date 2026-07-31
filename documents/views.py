import os
import logging

from django.conf import settings
from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from documents.models import Document, Chunk, ChatSession, ChatMessage
from documents.serializers import (
    DocumentSerializer, ChatSessionSerializer, ChatMessageSerializer,
)
from documents.services import ingestion, embeddings, rag

logger = logging.getLogger(__name__)


def index_view(request):
    """Serves the single-page frontend."""
    return render(request, 'documents/index.html')


class DocumentListCreateView(APIView):
    """GET: list uploaded documents. POST: upload + process a new one."""

    def get(self, request):
        docs = Document.objects.all()
        return Response(DocumentSerializer(docs, many=True).data)

    def post(self, request):
        upload = request.FILES.get('file')
        if not upload:
            return Response({'detail': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)

        ext = os.path.splitext(upload.name)[1].lower()
        if ext not in settings.ALLOWED_UPLOAD_EXTENSIONS:
            return Response(
                {'detail': f"Unsupported file type '{ext}'. Only PDF and DOCX are supported."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if upload.size > max_bytes:
            return Response(
                {'detail': f"File is too large. Max size is {settings.MAX_UPLOAD_SIZE_MB}MB."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_type = 'pdf' if ext == '.pdf' else 'docx'
        document = Document.objects.create(
            file=upload,
            original_filename=upload.name,
            file_type=file_type,
            status=Document.Status.PROCESSING,
        )

        try:
            self._process_document(document)
        except Exception as exc:
            logger.exception("Failed to process document %s", document.id)
            document.status = Document.Status.FAILED
            document.error_message = str(exc)
            document.save()
            return Response(
                DocumentSerializer(document).data,
                status=status.HTTP_201_CREATED,
            )

        return Response(DocumentSerializer(document).data, status=status.HTTP_201_CREATED)

    @staticmethod
    def _process_document(document: Document):
        chunks = ingestion.process_upload(document.file.path, document.file_type)
        embeddings.build_index(document.id, chunks)

        Chunk.objects.bulk_create([
            Chunk(document=document, order=i, text=text, vector_index_position=i)
            for i, text in enumerate(chunks)
        ])

        document.page_or_chunk_count = len(chunks)
        document.status = Document.Status.READY
        document.save()


class DocumentDetailView(APIView):
    """DELETE: remove a document, its chunks, and its vector index."""

    def delete(self, request, document_id):
        document = get_object_or_404(Document, id=document_id)
        embeddings.delete_index(document.id)
        document.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionCreateView(APIView):
    """POST: start a new chat session for a document."""

    def post(self, request, document_id):
        document = get_object_or_404(Document, id=document_id)
        if document.status != Document.Status.READY:
            return Response(
                {'detail': 'Document is not ready yet.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        session = ChatSession.objects.create(document=document)
        return Response(ChatSessionSerializer(session).data, status=status.HTTP_201_CREATED)


class SessionDetailView(APIView):
    """GET: fetch a session and its full message history."""

    def get(self, request, session_id):
        session = get_object_or_404(ChatSession, id=session_id)
        return Response(ChatSessionSerializer(session).data)


class MessageCreateView(APIView):
    """POST: ask a question in a session; runs the RAG pipeline and returns the answer."""

    def post(self, request, session_id):
        session = get_object_or_404(ChatSession, id=session_id)
        question = (request.data.get('content') or '').strip()
        if not question:
            return Response({'detail': 'content is required.'}, status=status.HTTP_400_BAD_REQUEST)

        user_message = ChatMessage.objects.create(
            session=session, role=ChatMessage.Role.USER, content=question,
        )

        history = [
            {'role': m.role, 'content': m.content}
            for m in session.messages.exclude(id=user_message.id)
        ]

        try:
            result = rag.answer_question(session.document, question, chat_history=history)
        except Exception as exc:
            logger.exception("RAG pipeline failed for session %s", session.id)
            return Response(
                {'detail': f"Something went wrong generating an answer: {exc}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        assistant_message = ChatMessage.objects.create(
            session=session, role=ChatMessage.Role.ASSISTANT, content=result['answer'],
        )
        assistant_message.source_chunks.set(result['chunks'])

        return Response(ChatMessageSerializer(assistant_message).data, status=status.HTTP_201_CREATED)
