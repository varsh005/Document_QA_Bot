import uuid
import django.db.models.deletion
import documents.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Document',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('file', models.FileField(upload_to=documents.models.upload_path)),
                ('original_filename', models.CharField(max_length=255)),
                ('file_type', models.CharField(choices=[('pdf', 'PDF'), ('docx', 'DOCX')], max_length=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('processing', 'Processing'), ('ready', 'Ready'), ('failed', 'Failed')], default='pending', max_length=15)),
                ('error_message', models.TextField(blank=True, default='')),
                ('page_or_chunk_count', models.PositiveIntegerField(default=0)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['-uploaded_at']},
        ),
        migrations.CreateModel(
            name='Chunk',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('order', models.PositiveIntegerField()),
                ('text', models.TextField()),
                ('vector_index_position', models.PositiveIntegerField()),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chunks', to='documents.document')),
            ],
            options={'ordering': ['order']},
        ),
        migrations.CreateModel(
            name='ChatSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='documents.document')),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='ChatMessage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role', models.CharField(choices=[('user', 'User'), ('assistant', 'Assistant')], max_length=10)),
                ('content', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('session', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='documents.chatsession')),
                ('source_chunks', models.ManyToManyField(blank=True, related_name='cited_in_messages', to='documents.chunk')),
            ],
            options={'ordering': ['created_at']},
        ),
    ]
