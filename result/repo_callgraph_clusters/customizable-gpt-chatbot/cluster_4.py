# Cluster 4

class TrainView(View):
    """
    View to train a Pinecone index
    """

    def get(self, request, object_id):
        if not request.user.is_staff and (not request.user.is_superuser):
            return HttpResponseForbidden("You don't have permission to access this page.")
        document = Document.objects.get(pk=object_id)
        index_name = settings.PINECONE_INDEX_NAME
        namespace = settings.PINECONE_NAMESPACE_NAME
        file_url = document.file.url
        response = requests.get(file_url)
        temp_dir = tempfile.mkdtemp()
        file_name = os.path.join(temp_dir, os.path.basename(file_url))
        with open(file_name, 'wb') as f:
            f.write(response.content)
        file_path = file_name
        build_or_update_pinecone_index(file_path, index_name, namespace)
        document.is_trained = True
        document.save()
        os.remove(file_path)
        os.rmdir(temp_dir)
        messages.success(request, 'Training complete.')
        admin_url = reverse('admin:training_model_document_change', args=[object_id])
        return HttpResponseRedirect(admin_url)

def get(self, request, object_id):
    if not request.user.is_staff and (not request.user.is_superuser):
        return HttpResponseForbidden("You don't have permission to access this page.")
    document = Document.objects.get(pk=object_id)
    index_name = settings.PINECONE_INDEX_NAME
    namespace = settings.PINECONE_NAMESPACE_NAME
    file_url = document.file.url
    response = requests.get(file_url)
    temp_dir = tempfile.mkdtemp()
    file_name = os.path.join(temp_dir, os.path.basename(file_url))
    with open(file_name, 'wb') as f:
        f.write(response.content)
    file_path = file_name
    build_or_update_pinecone_index(file_path, index_name, namespace)
    document.is_trained = True
    document.save()
    os.remove(file_path)
    os.rmdir(temp_dir)
    messages.success(request, 'Training complete.')
    admin_url = reverse('admin:training_model_document_change', args=[object_id])
    return HttpResponseRedirect(admin_url)

class Document(models.Model):
    CHOICES = (('FAISS', 'FAISS'), ('PINECONE', 'PINECONE'))
    file = models.FileField(upload_to=dynamic_upload_to)
    index_name = models.CharField(max_length=255)
    storage_type = models.CharField(max_length=255, choices=CHOICES)
    is_trained = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

    def file_name(self):
        return os.path.basename(self.file.name)

def file_name(self):
    return os.path.basename(self.file.name)

class DocumentAdmin(admin.ModelAdmin):
    """
    Admin View for Document
    """
    list_display = ('file_name', 'index_name', 'storage_type', 'is_trained', 'uploaded_at', 'train_button')
    search_fields = ('file', 'index_name', 'storage_type')
    list_filter = ('is_trained',)

    def train_button(self, obj):
        train_url = reverse('train_view', args=[obj.pk])
        return format_html('<a class="button" href="{}">{}</a>', train_url, 'Train')

def train_button(self, obj):
    train_url = reverse('train_view', args=[obj.pk])
    return format_html('<a class="button" href="{}">{}</a>', train_url, 'Train')

class FAISS(BaseFAISS):
    """
    FAISS is a vector store that uses the FAISS library to store and search vectors.
    """

    @classmethod
    def load(cls, file_path):
        with open(file_path, 'rb') as f:
            return pickle.load(f)

    def save(self, file_path):
        with open(file_path, 'wb') as f:
            pickle.dump(self, f)

    def add_vectors(self, new_embeddings):
        self.index.add(new_embeddings)

@classmethod
def load(cls, file_path):
    with open(file_path, 'rb') as f:
        return pickle.load(f)

def save(self, file_path):
    with open(file_path, 'wb') as f:
        pickle.dump(self, f)

